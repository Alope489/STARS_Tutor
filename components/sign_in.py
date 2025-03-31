from pymongo import MongoClient
import streamlit as st
import logging
from components.course_upload import course_upload

client = MongoClient("mongodb://localhost:27017/")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

db = client["user_data"]
users_collection = db["users"]
archive = client["chat_app"]
chats_collection = archive["chats"]

if 'courses_valid' not in st.session_state: 
    st.session_state.courses_valid = False

def validate_email(email):
    """Ensure the email ends with @fiu.edu."""
    return email.endswith("@fiu.edu")

def add_user(fname,lname,email, password,user_type,panther_id,courses):
    """Add a new user to the database."""
    if users_collection.find_one({"email": email}):
        return "Email already registered."
    #new users have had their course info approved, therefore their status is immediately pending approval
    users_collection.insert_one({"fname":fname,"lname":lname, "email": email, "password": password,"panther_id":panther_id,"user_type":user_type,"status":"pending_approval","courses":courses})
    logging.info(f"New user added: {email}")
    return "success"
def authenticate_user(email, password):
    """Authenticate user with email and password."""
    user = users_collection.find_one({"email": email, "password": password})
    if user:
        logging.info(f"User authenticated: {user['email']}")
    return user

def perform_sign_in_or_up():
     if st.session_state.auth_mode == "Sign In":
        st.subheader("Sign In")
        email = st.text_input("FIU Email Address")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = authenticate_user(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.fname = user['fname']
                st.session_state.panther_id = user['panther_id']
                st.session_state.user_type = user["user_type"]
                st.session_state.status = user["status"] or None
                st.success(f"Welcome back, {user['fname']}!")
                st.rerun()
            else:
                st.error("Invalid email or password.")
        if st.button("Sign Up"):
            st.session_state.auth_mode = "Sign Up"
            st.rerun()

     elif st.session_state.auth_mode == "Sign Up":
        st.subheader("Sign Up")
        email = st.text_input("FIU Email Address")
        fname = st.text_input('First Name')
        lname = st.text_input('Last Name')
        panther_id = st.text_input('Panther ID')
        password = st.text_input("Password", type="password")
        courses = course_upload()
        if st.button("Sign Up"):
            if not validate_email(email):
                st.error("Please use a valid FIU email address.")
            elif len(password) < 8 :
                st.error("Password must be at least 8 characters long.")
            elif len(panther_id)!=7 or not  panther_id.isdigit():
                st.error('Please fill in your panther id correctly.')
            elif st.session_state.courses_valid:
                result = add_user(fname,lname,email, password,"student",panther_id,courses)
                if result == "success":
                    st.success("Account created successfully! Please log in.")
                    st.session_state.auth_mode = "Sign In"
                    st.rerun()
                else:
                    st.error(result)
        if st.button("Sign In"):
            st.session_state.auth_mode = "Sign In"
            st.rerun()