# Import required modules
import time
import streamlit as st
from pymongo import MongoClient
import logging
from components.chatbot import Chatbot
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

# MongoDB Configuration


st.session_state.expander_open = False
# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.selected_completion = None
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "Sign In"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_bot" not in st.session_state:
    st.session_state.selected_bot = "tutorbot"  # Default bot selection

# App Structure
st.title("Stars Tutoring Chatbot")

if st.session_state.logged_in:
    # Display a success message temporarily
    # temp solution
    placeholder = st.empty()  # Create a placeholder
    placeholder.success(f"Welcome, {st.session_state.username}!")  # Show the success message
    time.sleep(2)  # Wait for 2 seconds
    placeholder.empty()  # Clear the message after 2 seconds

    

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
                    st.session_state.messages = chatbot.get_current_chat_history(user_id)

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
        
        

        chat_id = chatbot.get_current_chat_id(user_id)
        if chat_id!='deleted':
            st.session_state.messages = chatbot.get_current_chat_history(user_id)
        st.title(f"{st.session_state.selected_bot.capitalize()} Chat History")
   
        chat_id = chatbot.get_current_chat_id(user_id)
        if chat_id!='deleted':
            st.session_state.messages = chatbot.get_current_chat_history(user_id)
         

        # Fetch Recent Assistant Chats
        recent_chats = chatbot.get_recent_chats(user_id)

        if recent_chats:
            # Populate the selectbox with recent assistant messages
            def select_chat(chat_id):
                st.session_state.selected_chat_id = chat_id
                chatbot.set_current_chat_id(user_id, chat_id)
                st.session_state.messages = chatbot.get_current_chat_history(user_id)
            

            for chat in recent_chats:
                chat_id = chat["chat_id"]
                button_text = chat["content"][:50] + "..."
                
                if st.session_state.get("selected_chat_id") == chat_id:
                        button_text = f"🔵 {button_text}"

                st.sidebar.button(
                    button_text, 
                    key=chat_id, 
                    help="Click to open chat",
                    on_click=select_chat,
                    args=(chat_id,))
                
                    

            
            
        else:
            st.sidebar.warning("No chats available to display.")
            chatbot.start_new_chat(user_id)
            st.session_state.messages = chatbot.get_current_chat_history(user_id)

        st.markdown("<br><br>", unsafe_allow_html=True)

        col1,col_spacing ,col2 = st.columns([1,.5,1])
        with col1:
            with  st.popover("Delete"):      
                if st.button("Yes, Delete Current Chat!"):
                    chatbot.delete_chat(user_id)
                    st.success("chat Deleted!")
                    st.rerun()
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
        assistant_message = chatbot.generate_response(user_id,st.session_state.messages)
       
        st.chat_message("assistant").write(assistant_message)
    st.button('Fine Tune',type='primary',on_click=fine_tune)

    

else:
    perform_sign_in_or_up()