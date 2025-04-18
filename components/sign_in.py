from pymongo import MongoClient
import streamlit as st
import logging
from components.courses import course_upload
from components.db_functions import find_token,get_courses,add_courses_to_student
import hashlib
import os

client = MongoClient(st.secrets['MONGO_URI'])
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
import time

db = client["user_data"]
users_collection = db["users"]
archive = client["chat_app"]
chats_collection = archive["chats"]
st.markdown(
    """
    <style>
        .stButton > button {
            width: 100px;  /* Adjust width as needed */
        }
    </style>
    """,
    unsafe_allow_html=True
)
if 'courses_valid' not in st.session_state: 
    st.session_state.courses_valid = False

if 'generated_code' not in st.session_state:
    st.session_state.generated_code = ''
if 'user_type' not in st.session_state:
    st.session_state.user_type = 'student'

#Not used in code, to add admins manually. Need to get rid of components. inside sign_in.py and course.py to run in below
def add_admin(username,password):
    salt = os.urandom(16).hex()
    hashed_password = hash_password(password,salt)
    try:
        print(hashed_password)
        print(salt)
        user =users_collection.insert_one({"username":username,"password":hashed_password})
        user_found = users_collection.find_one({"username":username})
        return 'Admin Added'
    except Exception as e:
        return e

def hash_password(password, salt):
    """Hashes password with a given salt using SHA-256."""
    return hashlib.sha256((salt + password).encode()).hexdigest()
def validate_email(email):
     """Ensure the email ends with @fiu.edu."""
     return email.endswith("@fiu.edu")

def add_user(fname,lname,email, password,user_type,panther_id,courses):
     """Add a new user to the database."""
     if users_collection.find_one({"email": email}):
         return "Email already registered."
     salt = os.urandom(16).hex()
     hashed_password = hash_password(password,salt)
     users_collection.insert_one({"fname":fname,"lname":lname,"email":email,"user_type":user_type,"panther_id":panther_id,"courses":courses ,"password": hashed_password,"salt":salt,"status":"pending_approval"})

     logging.info(f"New user added: {email}, {email}")
     return "success"
#using hashing
def authenticate_user(email, password):
    """Authenticate user with email and password."""
    user_for_salt = users_collection.find_one({"email": email})
    if user_for_salt:
        input_password = hash_password(password, user_for_salt["salt"])
        user = users_collection.find_one({"email":email,"password":input_password})
        if user:
            logging.info(f"User authenticated: {user['email']}")
            return user
        return None


@st.dialog('Tutor Authentication Form')
def tutor_auth_form():
    auth_code = st.text_input('Insert Authentication Code')
    authenticate = st.button('Authenticate')
    if authenticate:
        current_token = find_token()
        if current_token and current_token['token']==auth_code:
            st.success('You have been authenticated!')
            st.session_state.user_type='tutor'
            time.sleep(2)
            st.rerun()
        else:
            st.error('That code is either incorrect or expired')
def unique_email(email):
    #returns True if it is a unique entry, unique email and panther id
    user_by_email = users_collection.find_one({"email":email})
    if user_by_email:
        return False
    return True
def unique_panther_id(panther_id):
    user_by_panther_id = users_collection.find_one({"panther_id":panther_id})
    if user_by_panther_id:
        return False 
    return True

def sign_in_form():
     #can be replaced with SSO.
     st.subheader("Sign In")
     email = st.text_input("FIU Email Address")
     password = st.text_input("Password", type="password")
     col1,col2,col3 = st.columns([1,1,2])
     with col1:
         st.empty()
     with col2:
        if st.button("Login"):
            user = authenticate_user(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.fname = user['fname']
                st.session_state.user_type = user["user_type"]
                #only for students/ tutors
                if 'panther_id' in user:
                    st.session_state.panther_id = user['panther_id']
                if 'status' in user:
                    st.session_state.status =user['status']
                st.success(f"Welcome back, {user['fname']}!")
                st.rerun()
            else:
                st.error("Invalid email or password.")
     with col3:
        if st.button("Sign Up"):
            st.session_state.auth_mode = "Sign Up"
            st.rerun()

def tutor_course_sign_up():
    courses = get_courses()
    merged_list = [f"{course['course_id']} - {course['course_name']}"for course in courses]
    course_strings = st.multiselect('Select your courses',merged_list)
    chosen_course_ids = [option.split(' - ')[0] for option in course_strings]
    #meant more for students, tutors just need a confirmation dialog.
    st.session_state.courses_valid=True
    return chosen_course_ids,course_strings

@st.dialog('Confirm your courses')
def tutor_course_confirmation(panther_id,courses,courses_strings,enrollment_type,user_type,fname=None,lname=None,email=None,password=None):
    st.write(courses_strings)
    approve = st.button('Confirm')
    if approve:
        if enrollment_type=='sign_up':
            process_user(fname,lname,email,password,user_type,panther_id,courses)
        if enrollment_type=='course_enrollment':
            add_courses_to_student(panther_id,courses)
        
        

def process_user(fname,lname,email,password,user_type,panther_id,courses):
    result = add_user(fname,lname,email, password,user_type,panther_id,courses)
    if result == "success":
        st.success("Account created successfully! Please log in.")
        time.sleep(2)
        st.session_state.auth_mode = "Sign In"
        st.rerun()
    else:
        st.error(result)

def sign_up_form():
    st.subheader("Sign Up")
    #  tutor_button = st.button('Are you a tutor?',key='tutor_button')
    email = st.text_input("FIU Email Address")
    fname = st.text_input('First Name')
    lname = st.text_input('Last Name')
    panther_id = st.text_input('Panther ID')
    password = st.text_input("Password", type="password")
    if st.session_state.user_type=='student':
        tutor_button = st.button('Tutor?',on_click=tutor_auth_form)
        courses = course_upload()
    else:
        courses,course_strings =tutor_course_sign_up()
    col1,col2,col3 = st.columns([1,1,2])
    with col1:
        st.empty()
    with col2:
        if st.button("Sign Up"):
            if not validate_email(email):
                st.error("Please use a valid FIU email address.")
            elif len(password) < 8 :
                st.error("Password must be at least 8 characters long.")
            elif not unique_email(email):
                st.error('This email is already registered!')
            elif not unique_panther_id(panther_id):
                st.error('This panther id is already registered!')
            elif len(panther_id)!=7 or not  panther_id.isdigit():
                st.error('Please fill in your panther id correctly.')
            elif st.session_state.courses_valid:
                #students have to go through course validation from courses.py and courses_valid will be True once validated. Tutors don't have validation just confirmation
                if st.session_state.user_type=='tutor':
                    tutor_course_confirmation(panther_id,courses,course_strings,'sign_up',"tutor",fname,lname,email, password)
                else:
                   process_user(fname,lname,email, password,"student",panther_id,courses)
    with col3:
        if st.button("Sign In"):
            st.session_state.auth_mode = "Sign In"
            st.rerun()
def perform_sign_in_or_up():
     if st.session_state.auth_mode == "Sign In":
        #With SSO: If not enrolled then post authentication redirect to sign up form. If not authenticated then redirect to failure page (if not existing)
        sign_in_form()
       
     elif st.session_state.auth_mode == "Sign Up":
        sign_up_form()

# if __name__ =="__main__":
#     print(add_admin('testadmin@fiu.edu',"testadmin123"))