# Import required modules
import time
import streamlit as st
from pymongo import MongoClient
import logging
import pandas as pd
from components.chatbot import Chatbot
from components.admin import mongo_uri,client,coursedb,users_collection,admin_panel
from dotenv import load_dotenv
from datetime import datetime
import uuid
import os
import json
import csv
import jsonlines
from components.fine_tuning import perform_fine_tuning,set_current_completion,add_examples,add_completions,fine_tune
from components.sign_in import validate_email,authenticate_user,add_user,perform_sign_in_or_up
load_dotenv()
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            min-width: 300px !important;
            max-width: 300px !important;
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
    st.session_state.username = ""
    st.session_state.user_type = ""
    st.session_state.student_status = ""
    st.session_state.selected_completion = None
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "Sign In"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_bot" not in st.session_state:
    st.session_state.selected_bot = "tutorbot"  # Default bot selection

# App Structure
# st.title("Stars Tutoring Chatbot")


if st.session_state.logged_in:
    #Admin UI
    if st.session_state.user_type =="admin":
        admin_panel()
    elif st.session_state.user_type=='tutor' or st.session_state.student_status=='approved':
        # Display a success message temporarily
        # temp solution
        placeholder = st.empty()  # Create a placeholder
        placeholder.success(f"Welcome, {st.session_state.username}!")  # Show the success message
        time.sleep(2)  # Wait for 2 seconds
        placeholder.empty()  # Clear the message after 2 seconds
        
        # st.success(f"Welcome, {st.session_state.username}!")
        user_id = st.session_state.username

    
        user_doc = users_collection.find_one({"username": user_id})
        # if user_doc[]
        user_courses = user_doc.get("courses", [])
    

        with st.sidebar:
            chatbot = Chatbot(
                api_key=st.secrets['OPENAI_API_KEY'],
                mongo_uri=mongo_uri,
                course_name=st.session_state.selected_bot  # Pass course_name instead of bot_type
            )   

            user_id = st.session_state.username
            user_courses = chatbot.get_courses(user_id)
            colA1,col_spacing1 ,colA2 = st.columns([1,.5,1])
            with colA1:
                if st.button("New Chat"):
                        chatbot.start_new_chat(user_id)
                        st.session_state.selected_chat_id = 0
                        st.success("New chat created!")
                        st.session_state.messages = chatbot.get_current_chat_history(user_id)
                
                        st.rerun()

            with colA2:
                with st.popover("Bot"):
                    bot_selection = st.radio("Choose your course:", user_courses,index=user_courses.index(st.session_state.selected_bot)) #This is to make sure when you create a new chat it stays in that bots page
                # Update session state if selection changes
                if bot_selection != st.session_state.selected_bot:
                    st.session_state.selected_bot = bot_selection
                    st.rerun()

                
                # Initialize chatbot with the selected bot
            #     if bot_selection != st.session_state.selected_bot:
            #         chatbot = Chatbot(
            #             api_key=st.secrets['OPENAI_API_KEY'],
            #             mongo_uri=mongo_uri,
            #             course_name=st.session_state.selected_bot  # Pass course_name instead of bot_type
            # ) 
            
            

            with st.sidebar:
                chatbot = Chatbot(
                    api_key=st.secrets['OPENAI_API_KEY'],
                    mongo_uri="mongodb://localhost:27017/",
                    course_name=st.session_state.selected_bot  # Pass course_name instead of bot_type
                )   

                user_id = st.session_state.username
                user_courses = chatbot.get_courses(user_id)
                colA1,col_spacing1 ,colA2 = st.columns([1,.5,1])
                with colA1:
                    if st.button("New Chat"):
                            chatbot.start_new_chat(user_id)
                            st.session_state.selected_chat_id = 0
                            st.success("New chat created!")
                            st.session_state.messages = chatbot.get_current_chat_history(user_id)
                    
                            st.rerun()

                with colA2:
                    with st.popover("Bot"):
                        bot_selection = st.radio("Choose your course:", user_courses,index=user_courses.index(st.session_state.selected_bot)) #This is to make sure when you create a new chat it stays in that bots page
                    # Update session state if selection changes
                    if bot_selection != st.session_state.selected_bot:
                        st.session_state.selected_bot = bot_selection
                        st.rerun()

                    
                    # Initialize chatbot with the selected bot
                    if bot_selection != st.session_state.selected_bot:
                        chatbot = Chatbot(
                            api_key=st.secrets['OPENAI_API_KEY'],
                            mongo_uri="mongodb://localhost:27017/",
                            course_name=st.session_state.selected_bot  # Pass course_name instead of bot_type
                ) 
                
            

            # User Input
            user_input = st.chat_input("Type your message here...")
            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})
            
                st.chat_message("user").write(user_input)
            
                # Generate and display response
                assistant_message = chatbot.generate_response(user_id,st.session_state.messages)
            
                st.chat_message("assistant").write(assistant_message)
            
            if st.session_state.user_type =='tutor':
                st.button('Fine Tune',type='primary',on_click=fine_tune)
            
            
            elif st.session_state.student_status =='pending_courses':
                pass
            elif st.session_state.student_status =='pending_approval':
                st.info('Your information is pending approval, please wait and you will be notified once approved.')
            elif st.session_state.student_status =='rejected':
                st.error('Your information has been rejected. Please contact adminstrator for more information ')
else:
    st.session_state.user_type = perform_sign_in_or_up()
    st.rerun()


