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
client = MongoClient("mongodb://localhost:27017/")
db = client["user_data"]
users_collection = db["users"]
archive = client["chat_app"]
chats_collection = archive["chats"]


# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "Sign In"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_bot" not in st.session_state:
    st.session_state.selected_bot = "tutorbot"  # Default bot selection

# Helper Functions
def validate_email(email):
    """Ensure the email ends with @fiu.edu."""
    return email.endswith("@fiu.edu")

def add_user(username, email, password):
    """Add a new user to the database."""
    if users_collection.find_one({"email": email}):
        return "Email already registered."
    users_collection.insert_one({"username": username, "email": email, "password": password})
    logging.info(f"New user added: {username}, {email}")
    return "success"

def authenticate_user(email, password):
    """Authenticate user with email and password."""
    user = users_collection.find_one({"email": email, "password": password})
    if user:
        logging.info(f"User authenticated: {user['username']}")
    return user
#update

# App Structure

if st.session_state.logged_in:
    # Display a success message temporarily
    # temp solution
    placeholder = st.empty()  # Create a placeholder
    placeholder.success(f"Welcome, {st.session_state.username}!")  # Show the success message
    time.sleep(2)  # Wait for 2 seconds
    placeholder.empty()  # Clear the message after 2 seconds
    
    # st.success(f"Welcome, {st.session_state.username}!")
    user_id = st.session_state.username
    user_doc = users_collection.find_one({"username": user_id})
    user_courses = user_doc.get("courses", [])
    # Initialize Chatbot based on selection
    
    # chatbot.set_current_chat_id(user_id,'f9d77b5e-cc99-4ae4-a123-a8f5afeb03f3')

    # Sidebar for bot selection
    with st.sidebar:
         
        chatbot = Chatbot(
            api_key=st.secrets['OPENAI_API_KEY'],
            mongo_uri="mongodb://localhost:27017/",
            course_name=st.session_state.selected_bot  # Pass course_name instead of bot_type
        )   

        
        colA1,col_spacing1 ,colA2 = st.columns([1,.5,1])
        with colA1:
            if st.button("Add New Chat"):
                    chatbot.start_new_chat(user_id)
                    st.session_state.selected_chat_id = 0
                    st.success("New chat created!")
                    st.session_state.messages = chatbot.get_current_chat_history(user_id)
            
                    st.rerun()

        with colA2:
            with st.popover("Select Bot"):
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
            # st.rerun()
        st.title(f"{st.session_state.selected_bot.capitalize()} Chat History")
   
        chat_id = chatbot.get_current_chat_id(user_id)
        if chat_id!='deleted':
            st.session_state.messages = chatbot.get_current_chat_history(user_id)
            # st.rerun()

        # Fetch Recent Assistant Chats
        recent_chats = chatbot.get_recent_chats(user_id)

        if recent_chats:
            # Populate the selectbox with recent assistant messages
            selected_chat_id = st.session_state.get("selected_chat_id")

            for chat in recent_chats:
                chat_id = chat["chat_id"]
                button_text = chat["content"][:50] + "..."
                
                if selected_chat_id == chat_id:
                        button_text = f"🔵 {button_text}"

                if st.sidebar.button(button_text, key=chat_id, help="Click to open chat"):
                    # Retrieve selected chat's history
                    st.session_state.selected_chat_id = chat_id
                    selected_chat_id = chat["chat_id"]
                    chatbot.set_current_chat_id(user_id, selected_chat_id)
                    st.session_state.messages = chatbot.get_current_chat_history(user_id)
                    st.rerun()
            
            
        else:
            st.sidebar.warning("No chats available to display.")
            chatbot.start_new_chat(user_id)
            st.session_state.messages = chatbot.get_current_chat_history(user_id)

        st.markdown("<br><br>", unsafe_allow_html=True)

        col1,col_spacing ,col2 = st.columns([1,.5,1])
        with col1:
            with  st.popover("Delete Chat"):      
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

            

    st.title(f"Welcome to the Stars Tutoring {st.session_state.selected_bot.capitalize()} Chatbot")


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
        
        # # Avoid duplicate assistant messages
        # if not st.session_state.messages or st.session_state.messages[-1]["content"] != assistant_message:
        #     st.session_state.messages.append({"role": "assistant", "content": assistant_message})
        st.chat_message("assistant").write(assistant_message)
        # st.rerun()

    

else:
    if st.session_state.auth_mode == "Sign In":
        st.subheader("Sign In")
        email = st.text_input("FIU Email Address")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = authenticate_user(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = user["username"]
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
        if st.button("Sign Up"):
            if not validate_email(email):
                st.error("Please use a valid FIU email address.")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters long.")
            else:
                result = add_user(username, email, password)
                if result == "success":
                    st.success("Account created successfully! Please log in.")
                    st.session_state.auth_mode = "Sign In"
                    st.rerun()
                else:
                    st.error(result)
        if st.button("Sign In"):
            st.session_state.auth_mode = "Sign In"
            st.rerun()
