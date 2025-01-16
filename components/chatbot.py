import streamlit as st
from openai import OpenAI
from pymongo import MongoClient

# Chatbot Configuration
class Chatbot:
    def __init__(self, api_key, mongo_uri):
        self.client = OpenAI(api_key=api_key)
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client["chat_app"]
        self.chats_collection = self.db["chats"]

    def save_chat_history(self, user_id, messages):
        chat_session = {"user_id": user_id, "messages": messages}
        self.chats_collection.insert_one(chat_session)

    def generate_response(self, user_id, messages):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            assistant_message = response.choices[0].message.content
            # Save updated chat history
            self.save_chat_history(user_id, messages)
            return assistant_message
        except Exception as e:
            return f"An error occurred: {e}"
