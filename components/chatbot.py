import streamlit as st
from openai import OpenAI
from pymongo import MongoClient
from datetime import datetime
import uuid
# Chatbot Configuration
class Chatbot:
    def __init__(self, api_key, mongo_uri):
        self.client = OpenAI(api_key=api_key)
        self.mongo_client = MongoClient(mongo_uri)
        self.users = self.mongo_client["user_data"]
        self.users_collection = self.users["users"]
        

    # def save_chat_history(self, user_id, messages):
    #     print('inside save chat history')
    #     #each user has to 2 chat histories, tutorbot and codebot histories. 
    #     #Each history has chats, represented by a dictionary containing the timestamp (of most recent message) as key and chat history message aray as value
    #     #we receive an updated message history
    #     chat_session = {"user_id": user_id, "messages": messages}
    #     self.chats_collection.insert_one(chat_session)
        # selected_bot = st.session_state.selected_bot
        # current_chat_timestamp = datetime.now().timestamp()
        # self.users_collection.update_one({"username":user_id},
        #                                  {"$set":{
        #                                      f"{selected_bot}.{current_chat_timestamp}" : messages
        #                                  }}
        #                                  )
        # print(self.users_collection)

    # def get_current_chat_id(self,user_id):
    #     print('inside get current chat id')
    #     #get currently selected chat from user, if none then generate one.
    #     user_doc = self.users.collection.find_one({'username':user_id})
    #     chat_id = None
    #     selected_bot = st.session_state.selected_bot
    #     if selected_bot =='TutorBot':
    #         chat_id = user_doc.get('current_chat_id_tutorbot')
    #         #if not found, create one.
    #         if not chat_id:
    #             chat_id = self.users_collection.update_one({"username":user_id},
    #                                              {"$set":{'current_chat_id_tutorbot':str(uuid.uuid4())}}
    #                                              )
    #     elif selected_bot =='CoderBot':
    #         chat_id = user_doc.get('current_chat_id_coderbot')
    #         if not chat_id:
    #             chat_id = self.users_collection.update_one({"username":user_id},
    #                                              {"$set":{'current_chat_id_coderbot':str(uuid.uuid4())}}
    #                                              )
    #     print(chat_id)
    #     return chat_id



    # def generate_response(self, user_id, messages):
    #     try:
    #         response = self.client.chat.completions.create(
    #             model="gpt-4o",
    #             messages=messages
    #         )
    #         assistant_message = response.choices[0].message.content
    #         # Save updated chat history
    #         # self.save_chat_history(user_id, user_input,assistant_message)
    #         print(self.get_current_chat_id(user_id))
    #         return assistant_message
    #     except Exception as e:
    #         return f"An error occurred: {e}"
