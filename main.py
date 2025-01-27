# Import required modules
import streamlit as st
from pymongo import MongoClient
import logging
from components.chatbot import Chatbot
from components.tutorbot import TutorBot
from components.codebot import CodeBot
from dotenv import load_dotenv
from datetime import datetime
import uuid
import os
load_dotenv()


# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# MongoDB Configuration
client = MongoClient("mongodb://localhost:27017/")
db = client["user_data"]
users_collection = db["users"]


# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "Sign In"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_bot" not in st.session_state:
    st.session_state.selected_bot = "TutorBot"  # Default bot selection

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

def start_new_chat(chatbot, user_id):    
    if st.session_state.selected_bot == "TutorBot": 
            
            #This creates a new id for the code
            new_chat_id = str(uuid.uuid4())
            initial_message = {"role": "assistant", "content": "Hi! This is the start of a new TutorBot chat."}

            # Add the new chat to the database and set it as the current chat
            result = chatbot.users_collection.update_one(
                {"username": user_id},
                {
                    "$set": {
                        f"tutor_chat_histories.{new_chat_id}": {
                            "timestamp": datetime.now().timestamp(),
                            "chat_history": [initial_message]
                        },
                        "current_chat_id_tutorbot": new_chat_id  # Update the current chat ID
                    }
                }
            )

            # Check if the new chat was created successfully
            if result.modified_count == 0:
                logging.error("Failed to create new chat in the database.")
                st.error("Could not create a new chat. Please try again.")
                return

    elif st.session_state.selected_bot == "CodeBot":
                #This creates a new id for the code
                new_chat_id = str(uuid.uuid4())
                initial_message = {"role": "assistant", "content": "Hi! This is the start of a new CoderBot chat."}

            # Add the new chat to the database and set it as the current chat
                result = chatbot.users_collection.update_one(
                {"username": user_id},
                {
                    "$set": {
                        f"coderbot_chat_histories.{new_chat_id}": {
                            "timestamp": datetime.now().timestamp(),
                            "chat_history": [initial_message]
                        },
                        "current_chat_id_coderbot": new_chat_id  # Update the current chat ID
                    }
                }
            )

            # Check if the new chat was created successfully
                if result.modified_count == 0:
                    logging.error("Failed to create new chat in the database.")
                    st.error("Could not create a new chat. Please try again.")
                    return


# App Structure
st.title("Welcome to the Stars Tutoring Chatbot")

if st.session_state.logged_in:
    st.success(f"Welcome, {st.session_state.username}!")

    # Sidebar for bot selection
    st.sidebar.title("Select Bot")
    bot_selection = st.sidebar.radio("Choose your bot:", ["TutorBot", "CodeBot"])
    st.session_state.selected_bot = bot_selection

    user_id = st.session_state.username

    # Initialize Chatbot based on selection
    if st.session_state.selected_bot == "TutorBot":
        chatbot = TutorBot(
            api_key=st.secrets['OPENAI_API_KEY'],
            mongo_uri="mongodb://localhost:27017/",
        )
    elif st.session_state.selected_bot == "CodeBot":
        chatbot = CodeBot(
            api_key=st.secrets['OPENAI_API_KEY'] ,
            mongo_uri="mongodb://localhost:27017/",
        )
    else:
        st.error("Invalid bot selection.")
    
    st.session_state.messages = chatbot.get_current_chat_history(user_id)
    # Ensure message history exists for the selected bot
    # if st.session_state.selected_bot not in st.session_state.messages:
    #     st.session_state.messages[st.session_state.selected_bot] = []

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
        
        # Avoid duplicate assistant messages
        if not st.session_state.messages or st.session_state.messages[-1]["content"] != assistant_message:
            st.session_state.messages.append({"role": "assistant", "content": assistant_message})
            st.chat_message("assistant").write(assistant_message)
        st.rerun()

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.messages = []
        st.rerun()

    if st.button("Add New Chat"):
        start_new_chat(chatbot, user_id)
        st.success("New chat created!")
        st.rerun()
        
        
        


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
