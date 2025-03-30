import streamlit as st
from openai import OpenAI
from pymongo import MongoClient
from datetime import datetime
import uuid
import logging
from components.ChatChainSingleton import ChatChainSingleton
from cachetools import cached, LFUCache, TTLCache
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.callbacks.base import BaseCallbackHandler
import re



# Chatbot Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Caching global
lfu_cache = LFUCache(maxsize=32) # Least Freq Used


class StreamlitCallbackHandler(BaseCallbackHandler):
    def __init__(self, container):
        self.container = container
        self.text = ""

    def on_llm_new_token(self, token: str, **kwargs):
        self.text += token
        self.container.markdown(self.text + "▌")  # optional typing effect

    def get_response(self):
        return self.text.strip()
    
def format_latex_blocks(text):
        """
        Detects LaTeX math inside the chat responses [ ... ] and converts to $$ ... $$ for Streamlit rendering.
        """
        text = re.sub(r'\\text\{(.*?)\}', r'\\mathrm{\1}', text)
        text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text)  # Handle \( ... \) → $...$ 
        text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text) # Handle \[ ... \] → $$...$$
        text = re.sub(r'\[\s*(.*?)\s*\]', r'$$\1$$', text) # [ ... ] → $$ ... $$ 

        # Ensure math blocks are surrounded by newlines so Streamlit renders them properly
        text = re.sub(r'\$\$(.*?)\$\$', r'\n\n$$\1$$\n\n', text, flags=re.DOTALL) 
        return text

class Chatbot:
    def __init__(self, api_key, mongo_uri, course_name): 
        self.client = OpenAI(api_key=api_key)
        self.mongo_client = MongoClient(mongo_uri)
        self.users = self.mongo_client["user_data"]
        self.users_collection = self.users["users"]
        self.archive = self.mongo_client["chat_app"]
        self.chats_collection = self.archive["chats"]
        self.bot_type = course_name  
        self.chain = ChatChainSingleton().chain
        self.prompt = ChatChainSingleton().prompt

    def generate_chat_summary(self,chat_history):
        """start_new_chat
        Generate a summary of the chat using LangChain.
        """
        prompt_template = """
        Generate a concise, engaging title summarizing the following conversation. The title should be short (5-7 words), clear, and relevant to the topic. Here is the conversation:

        {chat_text}

        One-line summary:
        """

        llm = ChatOpenAI(
            temperature = 0,
            model_name="gpt-3.5-turbo-0125",
            api_key=st.secrets['OPENAI_API_KEY']
        )

        prompt = PromptTemplate(template = prompt_template, input_variables = ["chat_text"])
        chain = LLMChain (llm= llm, prompt=prompt)

        chat_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])

        
        summary = chain.run(chat_text = chat_text)
        return summary.strip()


    def set_current_chat_id(self,user_id,chat_id):
        #coderbot not codebot!
        self.users_collection.update_one({"username":user_id},
                                         {"$set":{f'current_chat_id_{self.bot_type}':chat_id}}
                                         )
        return chat_id
        
    def get_current_chat_id(self,user_id):
        #get currently selected chat from user, if none then generate one.
        user_doc = self.users_collection.find_one({'username':user_id})
        chat_id = user_doc.get(f'current_chat_id_{self.bot_type}')
        #if not found, create one.
        if not chat_id:
            new_chat_id = str(uuid.uuid4())
            chat_id = new_chat_id
            self.users_collection.update_one({"username":user_id},
                                                 {"$set":{f'current_chat_id_{self.bot_type}':new_chat_id}}
                                                 )
        return chat_id
    
    def get_current_chat_history(self,user_id):
        chat_id = self.get_current_chat_id(user_id)
        #when deleting a chat chat_id is not initially known until the selectbox refreshes.
        if chat_id:
            user_doc = self.users_collection.find_one({'username':user_id})
            chat_histories = user_doc.get(f'{self.bot_type}_chat_histories')
            if not chat_histories:
                #create one and return original assistant prompt
                original_message = {"role": "assistant","content":f"Hi! I am a {self.bot_type} fined tuned bot, I will help you with any question regarding this domain!"}
                self.users_collection.update_one({"username":user_id},
                                                {"$set":{f"{self.bot_type}_chat_histories":{chat_id:{'timestamp':datetime.now().timestamp(),'chat_history': [original_message]}}}}
                                                )
                return [original_message]
            current_chat = chat_histories[chat_id]['chat_history']
            return current_chat
        return None
    def get_courses(self,user_id):
        user_doc = user_doc = self.users_collection.find_one({'username':user_id})
        user_courses = user_doc.get("courses", [])
        return user_courses
    
    def add_messages_to_chat_history(self,user_id,new_messages):
        chat_id = self.get_current_chat_id(user_id)
        chat_history_path = f'{self.bot_type}_chat_histories.{chat_id}.chat_history'
        chat_timestamp_path = f'{self.bot_type}_chat_histories.{chat_id}.timestamp'
        summary_path = f'{self.bot_type}_chat_histories.{chat_id}.summary'
        
        self.users_collection.update_one({'username':user_id},
                                         {'$push':{chat_history_path:{"$each":new_messages}}, #push is to push values into an existing object. Each is for pushing multiple values into that object
                                          '$set':{chat_timestamp_path: datetime.now().timestamp()}} # set is to update a specfic field in a object.
                                        ) 
        
        # Get chat out of cache if chat is updated
        if chat_id in lfu_cache:
            del lfu_cache[chat_id]


        
        user_doc = self.users_collection.find_one({'username': user_id})
        chat_history = user_doc[f'{self.bot_type}_chat_histories'][chat_id]['chat_history']

        summary = self.generate_chat_summary(chat_history)
        self.users_collection.update_one(
            {'username': user_id},
            {'$set': {summary_path: summary}}
    )

        if 'current_summary' not in st.session_state:
            st.session_state.current_summary = {}
        st.session_state.current_summary[chat_id] = summary


        #in front end, it is added to the session state automatically
        logging.info('Added message successfully')
        return 'added successfully'
    
    def get_all_chat_ids(self,user_id):
        user_doc = self.users_collection.find_one({'username':user_id})
        chat_histories_object = user_doc.get(f'{self.bot_type}_chat_histories')
        chat_ids = chat_histories_object.keys()
        self.update_chat_summary(user_id, chat_id, chat_history)
        return list(chat_ids)
    
    def start_new_chat(self,user_id): 
            #This creates a new id for the code
            new_chat_id = str(uuid.uuid4())
            initial_message = {f"role": "assistant", "content": f"Hi! This is the start of a new {self.bot_type} chat."}

        # Add the new chat to the database and set it as the current chat
            result = self.users_collection.update_one(
            {"username": user_id},
            {
                "$set": {
                    f"{self.bot_type}_chat_histories.{new_chat_id}": {
                        "timestamp": datetime.now().timestamp(),
                        "chat_history": [initial_message],
                        "summary": f"New {self.bot_type} chat"
                    },
                    f"current_chat_id_{self.bot_type}": new_chat_id  # Update the current chat ID
                }
            }
        )

        # Check if the new chat was created successfully
            if result.modified_count == 0:
                logging.error("Failed to create new chat in the database.")
                st.error("Could not create a new chat. Please try again.")
                return
            
    @cached(cache=lfu_cache)
    def get_recent_chats(self,user_id):
        """
        Fetch recent assistant messages for the selected bot's chat history.
        """
        user_data = self.users_collection.find_one({"username": user_id})
        if not user_data:
            st.warning("No user data found.")
            return []
        chat_key = f'{self.bot_type}_chat_histories'
        chat_histories = user_data.get(chat_key, {})
        if not chat_histories:
            st.warning(f"No chat history found for {st.session_state.selected_bot}.")
            return []



        # Extract messages and timestamps
        recent_chats = [
        {
            "chat_id": chat_id,
            "content": chat_data.get("summary","No summary available"),
            "timestamp": chat_data.get("timestamp", datetime.now().timestamp())
        }
        for chat_id, chat_data in chat_histories.items()
    ]

        # Sort chats by timestamp in descending order
        recent_chats = sorted(
                recent_chats,
                key=lambda x: x["timestamp"],
                reverse=True,
            )

        return recent_chats
    
    def delete_chat(self,user_id):
            # Get the user's current chat ID
        user_doc = self.users_collection.find_one({"username": user_id})
        current_chat_id = user_doc.get(f"current_chat_id_{self.bot_type}")
        if current_chat_id:
            chat_contents = user_doc.get(f"{self.bot_type}_chat_histories", {}).get(current_chat_id, {})
            if chat_contents:
              chat_entry = {
                "user_id": user_id,
                "chat_id": current_chat_id,
                "messages": chat_contents  
            }
            result = self.chats_collection.insert_one(chat_entry)
            logging.info(f"Inserted Chat ID: {result.inserted_id}")
            self.users_collection.update_one(
                    {"username": user_id},
                    {
                    "$unset": {f"{self.bot_type}_chat_histories.{current_chat_id}": ""},
                    "$set": {f"current_chat_id_{self.bot_type}": None}  # Reset the current chat ID
                    }
                )
        
        
        self.set_current_chat_id(user_id,'deleted')
        logging.info(f"Chat with ID {current_chat_id} deleted successfully.")

        recent_chats = self.get_recent_chats(user_id)

        new_chat_id = next((chat["chat_id"] for chat in recent_chats if chat["chat_id"] != current_chat_id), None)


        # Notify user
        if new_chat_id:
            self.set_current_chat_id(user_id, new_chat_id)
            st.session_state.selected_chat_id = new_chat_id
            st.session_state.messages = self.get_current_chat_history(user_id)
            st.success("Chat deleted successfully! Switched to the most recent chat.")
        else:
            self.set_current_chat_id(user_id, None)
            st.session_state.selected_chat_id = None
            st.session_state.messages = []
            st.warning("Chat deleted. No chats available.")

        st.rerun()

        
    def generate_chats(self,user_id):
                recent_chats = self.get_recent_chats(user_id)

                if recent_chats:
                    # Populate the selectbox with recent assistant messages
                    def select_chat(chat_id):
                        st.session_state.selected_chat_id = chat_id
                        self.set_current_chat_id(user_id, chat_id)
                        st.session_state.messages = self.get_current_chat_history(user_id)
                    

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
                    self.start_new_chat(user_id)
                    st.session_state.messages = self.get_current_chat_history(user_id)

    def generate_response(self, user_id, messages):
        try:
            logging.info("Generating response...")
            user_message = messages[-1]["content"]
            history = messages[:-1]

            prompt_values = {
                "input": user_message,
                "history": [
                    {"role": msg["role"], "content": msg["content"]} for msg in history
                ],
            }

            with st.chat_message("assistant"):
                container = st.empty()
                stream_handler = StreamlitCallbackHandler(container)

                llm = ChatOpenAI(
                    temperature=0.5,
                    model_name="gpt-3.5-turbo-0125",
                    streaming=True,
                    api_key=st.secrets['OPENAI_API_KEY'],
                    callbacks=[stream_handler]
                )

                chain = LLMChain(llm=llm, prompt=self.prompt)
                chain.invoke(prompt_values)

                assistant_message = stream_handler.get_response()
                assistant_message = format_latex_blocks(assistant_message)

            #add to DB
            new_messages = [{'role':'user','content':user_message},{'role':'assistant','content':assistant_message}]
            self.add_messages_to_chat_history(user_id,new_messages)

            # Re-fetch and store in cache
            self.get_recent_chats(user_id)

            logging.info("Response generated.")
            return assistant_message
        
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            return f"An error occurred: {e}"
        