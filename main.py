# Import required modules
import time
import streamlit as st
from pymongo import MongoClient
import logging
import pandas as pd
from components.chatbot import Chatbot
from components.admin import admin_panel
from dotenv import load_dotenv
from datetime import datetime
import uuid
import os
import json
import csv
import jsonlines
from components.fine_tuning import perform_fine_tuning,set_current_completion,fine_tune
from components.sign_in import validate_email,authenticate_user,add_user,perform_sign_in_or_up,tutor_course_confirmation,tutor_course_sign_up
from components.db_functions import get_course_dict,add_courses_to_student,get_user_courses,get_bot_competions,get_current_semester
from components.courses import course_upload
load_dotenv()
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            min-width: 340px !important;
            max-width: 340px !important;
            overflow: hidden !important;  /* Prevents resizing */
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")



st.session_state.expander_open = False
# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    #this is to initialize, but within sign up it get filled in. for username, user type and student status.
    st.session_state.fname = ""
    st.session_state.panther_id = ""
    #can be changed to if signing it and confirmed to be admin/tutor. Or if signing up and authenticated as a tutor
    st.session_state.user_type = "student"
    st.session_state.status = ""
    st.session_state.selected_completion = None
    st.session_state.generated_code = ""
    st.session_state.current_semester =get_current_semester()
    st.session_state.user_courses = []
    st.session_state.user_course_dict = {}
    st.session_state.course_names = []
    st.session_state.selected_bot_name = "tutorbot"
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "Sign In"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_bot" not in st.session_state:
    #selected bot is course_id for course specific bots 
    st.session_state.selected_bot = "tutorbot"  
if "show_fine_tune" not in st.session_state:
    st.session_state.show_fine_tune = False

# App Structure, don't display in admin panel
if not st.session_state.user_type=='admin':
    st.title("Stars Tutoring Chatbot")


if st.session_state.logged_in:
    #Admin UI
    if st.session_state.user_type =="admin":
        admin_panel()
    #For approved students/ tutors
    elif st.session_state.status=='approved':
        #set session states
        if not st.session_state.user_courses:
            st.session_state.user_courses = get_user_courses(st.session_state.panther_id)
        if not st.session_state.user_course_dict:
            st.session_state.user_course_dict = get_course_dict(st.session_state.user_courses)
        if not st.session_state.course_names:
            st.session_state.course_names =  ['tutorbot','codebot'] +list(st.session_state.user_course_dict.keys())

        with st.sidebar:
            #streamlit reruns main every time, hence this will be reinitialized every run to sync with session state selected_bot
            chatbot = Chatbot(
            api_key=st.secrets['OPENAI_API_KEY'],
            mongo_uri="mongodb://localhost:27017/",
            course_name=st.session_state.selected_bot  # Pass course_name instead of bot_type
        )   
            user_id = st.session_state.panther_id

            chat_id = chatbot.get_current_chat_id(user_id)
            chat_history = chatbot.get_current_chat_history(user_id) if chat_id != 'deleted' else []
            st.session_state.selected_chat_id = chat_id
            st.session_state.messages = chat_history

            
            colA1,col_spacing1 ,colA2 = st.columns([1,.8,1])
            with colA1:
                if st.button("New Chat"):
                        chatbot.start_new_chat(user_id)
                        new_chat_id = chatbot.get_current_chat_id(user_id)
                        st.session_state.selected_chat_id = new_chat_id 
                        st.session_state.messages = chatbot.get_current_chat_history(user_id)
                        

            with colA2:
                with st.popover("Bot"):
                    #it is important to keep selected bot as the course id (exception for tutorbot and codebot), hence course dict is crucial
                    bot_selection = st.radio("Choose your course:", st.session_state.course_names) 

                    if bot_selection!= st.session_state.selected_bot_name:
                        print(f'bot selection : {bot_selection} selected bot : {st.session_state.selected_bot}')
                        st.session_state.selected_bot_name = bot_selection
                        course_dict = st.session_state.user_course_dict
                        st.session_state.selected_bot= course_dict[bot_selection] if bot_selection in course_dict else bot_selection 
                        st.rerun()
                
  
            st.title(f"{st.session_state.selected_bot_name.capitalize()} Chat History")
            chatbot.generate_chats(user_id)
            
        
            st.markdown("<br><br>", unsafe_allow_html=True)

            col1,col_spacing ,col2 = st.columns([1,.8,1])
            with col1:
                with  st.popover("Delete"):      
                    if st.button("Yes, Delete Current Chat!"):
                        chatbot.delete_chat(user_id)
                                  
            with col2:
                if st.button("Logout"):
                    st.session_state.logged_in = False
                    st.session_state.username = ""
                    st.session_state.messages = []
                    st.rerun()  
                    
                
        # Display chat history for the selected bot
        
        for message in st.session_state.messages:
            st.chat_message(message["role"]).write(message["content"])

        # User Input
        user_input = st.chat_input("Type your message here...")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
        
            st.chat_message("user").write(user_input)
        
            # Generate and display response
            with st.spinner("Writing..."):
                assistant_message = chatbot.generate_response(user_id,st.session_state.messages)

        #only avaialble if tutor, 1 chatbot completion available and has completion data
        if st.session_state.user_type == "tutor" and len(st.session_state.messages) > 1:
              model_completions = get_bot_competions(st.session_state.selected_bot)
              if model_completions:
                fine_tune_button = st.button('Fine Tune')
                if fine_tune_button:
                        fine_tune()
        
    elif st.session_state.status =='pending_courses':
        #this is for old students/tutors who are logging into new semester.
        if st.session_state.user_type=='student':
            courses = course_upload()
            validate = st.button('validate')
            #validate button clicked and it successfully returns courses, no errors.
            if validate and courses:
                add_courses_to_student(st.session_state.panther_id,courses)
                time.sleep(3)
                st.rerun()
        else:
            course_ids, course_strings = tutor_course_sign_up()
            submit = st.button('Submit',on_click=tutor_course_confirmation,args=[st.session_state.panther_id,course_ids,course_strings,'course_enrollment'])

    elif st.session_state.status =='pending_approval':
        st.info('Your information is pending approval, please wait and you will be notified once approved.')
    elif st.session_state.status =='rejected':
        st.error('Your information has been rejected. Please contact adminstrator for more information: arehman@fiu.edu')
else:
    perform_sign_in_or_up()


