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

def validate_email(email):
    """Ensure the email ends with @fiu.edu."""
    return email.endswith("@fiu.edu")

def add_user(username, email, password,user_type):
    """Add a new user to the database."""
    if users_collection.find_one({"email": email}):
        return "Email already registered."
    student_status = ""
    if user_type=="student":
        student_status="pending_courses"
    else:
        student_status =None
    users_collection.insert_one({"username": username, "email": email, "password": password,"user_type":user_type,"student_status":student_status})
    logging.info(f"New user added: {username}, {email}")
    return "success"
def authenticate_user(email, password):
    """Authenticate user with email and password."""
    user = users_collection.find_one({"email": email, "password": password})
    if user:
        logging.info(f"User authenticated: {user['username']}")
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
                st.session_state.username = user["username"]
                st.session_state.user_type = user["user_type"]
                st.session_state.student_status = user["student_status"] or None
                st.success(f"Welcome back, {user['username']}!")
                st.rerun()
            else:
                st.error("Invalid email or password.")
        if st.button("Sign Up"):
            st.session_state.auth_mode = "Sign Up"
            st.rerun()

     elif st.session_state.auth_mode == "Sign Up":
        st.subheader("Sign Up")
        username = st.text_input("Username")
        email = st.text_input("FIU Email Address")
        password = st.text_input("Password", type="password")
        course_upload()
        if st.button("Sign Up"):
            if not validate_email(email):
                st.error("Please use a valid FIU email address.")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters long.")
            else:
                result = add_user(username, email, password,"student")
                if result == "success":
                    st.success("Account created successfully! Please log in.")
                    st.session_state.auth_mode = "Sign In"
                    st.rerun()
                else:
                    st.error(result)
        if st.button("Sign In"):
            st.session_state.auth_mode = "Sign In"
            st.rerun()