# Import required modules
import time
import streamlit as st
from pymongo import MongoClient
import logging
import pandas as pd
from components.chatbot import Chatbot
from dotenv import load_dotenv
from datetime import datetime
import uuid
import os
import json
import csv
import jsonlines
from components.system_prompt import system_prompt
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

coursedb = client['courses']
course_collection = coursedb['course_list']


st.session_state.expander_open = False
# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_type = ""
    st.session_state.selected_completion = None
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

def set_current_completion(completion):
    st.session_state.selected_completion = completion

def add_examples(selected_bot,input,output):
    #input is the user question. Output is the questions plus user answers
    new_entry = {'input':input,'output':output}
    with jsonlines.open(f'components/examples/{selected_bot}.jsonl','a') as writer:
        writer.write(new_entry)
    st.success('Created Few shot prompt and completion for training!')

def add_completions(prompt,answer):
    """
    {"messages": [{"role": "system", "content": "Marv is a factual chatbot that is also sarcastic."}, {"role": "user", "content": "What's the capital of France?"}, {"role": "assistant", "content": "Paris, as if everyone doesn't know that already."}]}
    """
    completion = {"messages":[{"role":"system","content":system_prompt},{"role":"user","content":prompt},{"role":"assistant","content":answer}]}
    with jsonlines.open('components/completions.jsonl','a') as writer:
        writer.write(completion)

@st.dialog('Help fine tune this model!')
def fine_tune():
    messages=  st.session_state.messages
    with st.expander('View Completions',expanded=st.session_state.expander_open):
        for i in range(2,len(messages),2):
                question = messages[i-1]['content']
                answer = messages[i]['content']
                if len(answer)>200:
                    answer = answer[:200] + '...'
                message = f'Question: {question} \n Answer: {answer}'
                completion = {'Question':question,'Answer':answer}
                st.json(completion)
                st.button('Select',key=i,on_click=set_current_completion,args=[completion])
   
    selected_completion = st.session_state.selected_completion
    if selected_completion:
        with st.expander('Perform Fine Tuning'):
            st.write(selected_completion)
            with st.form('my_form',clear_on_submit=True):
                follow_up_question_needed = st.selectbox('Are Follow up questions needed here?',('Yes','No'),index=None,placeholder='Yes/No')
                code_accuracy = st.selectbox('How accurately does the generated code perform the task?',('Failure','Slightly','Moderately','Highly'),index=None,placeholder='Select Accuracy')
                requirements_fufilled = st.selectbox('Does the generated code fulfill the requirements?',('Yes','No'),index=None,placeholder='Yes/No')
                final_answer = st.text_area('Preferred Answer: ')

                example = f"""Are Follow up questions needed here? {follow_up_question_needed}.How accurately does the generated code perform the task? : It {code_accuracy} performs the task
                    Does the generated code fulfill the requirements? : {requirements_fufilled}. Final Answer : {final_answer}
                """
                submitted = st.form_submit_button("Submit")
                if submitted:
                    add_examples(st.session_state.selected_bot,selected_completion['Question'],example)
                    add_completions(selected_completion['Question'],final_answer)
                # st.button('Submit',on_click=add_examples,args=[st.session_state.selected_bot,selected_completion['Question'],example])
 


# App Structure


def get_courses():
    courses = list(course_collection.find({}))
    return courses


if st.session_state.logged_in:
        
    if st.session_state.user_type =="admin":
        st.title("Welcome to the admin dashboard")
        st.write("Admin dashboard to add or remove courses")
        courses = get_courses()

        if not courses:
            st.write("no courses found")
        else:
            st.write("some courses:")
            df = pd.DataFrame(courses, columns=['course_name', 'course_code', 'course_id'])


            st.table(df)
            
            # if st.button("Add new course"):
                

        

    

    else:
        st.title("Welcome to the Stars Tutoring Chatbot")
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
                # st.session_state.selected_completion = st.session_state.messages[-1]
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
        
            st.chat_message("assistant").write(assistant_message)
            # st.rerun()
        st.button('Fine Tune',type='primary',on_click=fine_tune)
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

                #Added this line to add a new state for the user type. This will have to eb used for the tutors but also for the admin panel rn.
                st.session_state.user_type = user["user_type"]

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
