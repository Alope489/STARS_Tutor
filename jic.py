import streamlit as st
from pymongo import MongoClient
import logging
from components.chatbot import Chatbot
from components.tutorbot import TutorBot
from components.codebot import CodeBot
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# MongoDB Configuration
client = MongoClient("mongodb://localhost:27017/")
db = client["user_data"]
users_collection = db["users"]
#add key here

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "Sign In"
if "messages" not in st.session_state:
    st.session_state.messages = {}
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
            api_key=os.getenv("OPENAI_API_KEY"),
            mongo_uri="mongodb://localhost:27017/",
        )
    elif st.session_state.selected_bot == "CodeBot":
        chatbot = CodeBot(
            api_key=os.getenv("OPENAI_API_KEY"),
            mongo_uri="mongodb://localhost:27017/",
        )
    else:
        st.error("Invalid bot selection.")

    # Ensure message history exists for the selected bot
    if st.session_state.selected_bot not in st.session_state.messages:
        st.session_state.messages[st.session_state.selected_bot] = []

    # Display chat history for the selected bot
    for message in st.session_state.messages[st.session_state.selected_bot]:
        st.chat_message(message["role"]).write(message["content"])

    # User Input
    user_input = st.chat_input("Type your message here...")
    if user_input:
        # Append user's message to the chat history
        st.session_state.messages[st.session_state.selected_bot].append(
            {"role": "user", "content": user_input}
        )
        st.chat_message("user").write(user_input)

        # Call the chatbot and get a response
        assistant_message = chatbot.generate_response(
            user_id,
            [{"role": "user", "content": user_input}],  # Only send the new user input
        )

        # Append the assistant's response to the chat history
        st.session_state.messages[st.session_state.selected_bot].append(
            {"role": "assistant", "content": assistant_message}
        )
        st.chat_message("assistant").write(assistant_message)

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.messages = {}
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
