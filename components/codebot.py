# components/tutorbot.py
import os
from components.chatbot import Chatbot
from typing import Any
from langchain.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts.example_selector.semantic_similarity import SemanticSimilarityExampleSelector
import logging
import uuid
import streamlit as st
from datetime import datetime
import json
# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Custom selector with logging
class LoggingSemanticSimilarityExampleSelector(SemanticSimilarityExampleSelector):
    def select_examples(self, input_variables):
        logging.info("Few-shot examples selected.")
        return super().select_examples(input_variables)

# Singleton class for LangChain ChatChain
class ChatChainSingleton:
    _instance = None
    chain = None
    prompt = None  # Store final_prompt here
    model = "gpt-4o"

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            logging.info("ChatChainSingleton instance created.")
            cls._instance = super().__new__(cls)
            cls.chain = cls.initialize_chain(cls.model)
        return cls._instance

    @classmethod
    def initialize_chain(cls, model: str = "gpt-4o") -> Any:
        logging.info("Initializing ChatChain.")
        with open('examples.json','r') as file:
            examples = json.load(file)['codebot']

        try:
            embeddings = OpenAIEmbeddings(api_key=st.secrets['OPENAI_API_KEY'] )
            to_vectorize = [" ".join(example.values()) for example in examples]
            vectorstore = Chroma.from_texts(to_vectorize, embeddings, metadatas=examples, persist_directory= r"Documents")
            logging.info("Chroma initialized.")
        except Exception as e:
            logging.error(f"Chroma initialization failed: {e}")
            return None

        example_selector = LoggingSemanticSimilarityExampleSelector(vectorstore=vectorstore, k=2)

        few_shot_prompt = FewShotChatMessagePromptTemplate(
            input_variables=["input"],
            example_selector=example_selector,
            example_prompt=ChatPromptTemplate.from_messages(
                [("human", "{input}"), ("ai", "{output}")]
            ),
        )

        #Assemble the final prompt template
        final_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "You are participating in an educational game designed to help users learn how to build programs with Language Learning Models (LLMs). The game operates as follows:\n\n"
                        "- **User Provides a Topic**: The user will give you a programming topic or concept they are interested in exploring.\n"
                        "- **Suggest a Mode**: Based on the topic, you will suggest one of two modes to proceed with:\n"
                        "  - **Prompt to Code**: You provide a programming prompt, and the user attempts to write the code that fulfills the requirements.\n"
                        "  - **Code to Prompt**: You provide a piece of code, and the user attempts to write a prompt that would generate such code.\n"
                        "- **Educational Interaction**: Engage with the user to help them understand how prompts influence code generation in LLMs. Your goal is to enhance their problem-solving skills and comprehension of programming concepts.\n\n"
                        "**Your Responsibilities:**\n\n"
                        "- **Guidance and Exploration**: Encourage the user to think critically by asking probing questions and offering explanations of relevant concepts.\n"
                        "- **Concept Clarification**: Break down technical topics and programming techniques into clear, accessible explanations tailored to the user's understanding.\n"
                        "- **Feedback and Evaluation**: After the user provides their response, evaluate how well it matches the expected code or prompt. Offer constructive feedback to guide their learning.\n"
                        "- **Promote Independent Learning**: Direct the user to additional resources or materials to deepen their understanding, without giving away the solution.\n\n"
                        "**Restrictions:**\n\n"
                        "- **Do Not Provide Direct Solutions**: Under no circumstances should you complete or solve the assignment, write the required code, or provide the direct answer for the user.\n"
                        "- **Use Pseudocode When Necessary**: If you need to illustrate a concept that involves coding, use pseudocode instead of actual code.\n"
                        "- **Formatting Guidelines**:\n"
                        "  - Format your answers in **markdown**.\n"
                        "  - If you include code snippets, enclose them in code blocks using backticks, like this:\n"
                        "    ```python\n"
                        "    print(\"Hello, world!\")\n"
                        "    ```\n"
                        "  - For equations, use LaTeX formatting, for example: $$ y = mx + b $$.\n\n"
                        "**Example Interaction Flow:**\n\n"
                        "1. **User**: *\"I'd like to learn about sorting algorithms.\"*\n"
                        "2. **You**: *\"Great! Let's proceed with the 'Prompt to Code' mode. I'll give you a prompt, and you can attempt to write the code.\n\n"
                        "**Prompt**: Write a function that implements the bubble sort algorithm on a list of integers.\"*\n"
                        "3. **User**: *[Provides their code attempt]*\n"
                        "4. **You**: *\"Your code is a good start! It correctly sets up the function and loops, but there are some issues with how the elements are compared and swapped. Let's review how the inner loop should work in bubble sort...\"*\n\n"
                        "By following these guidelines, you'll help the user enhance their understanding of programming concepts and improve their ability to work with LLMs in code generation tasks."
                    ),
                ),
                few_shot_prompt.format(),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )

        chat_model = ChatOpenAI(
            model=model,
            temperature=0.0,
            api_key=st.secrets['OPENAI_API_KEY']
        )
        chain = final_prompt | chat_model

        cls.prompt = final_prompt
        cls.chain = chain
        logging.info("ChatChain ready.")
        return chain

    @staticmethod
    def change_model(new_model: str):
        logging.info(f"Model changed to: {new_model}")
        ChatChainSingleton.model = new_model
        ChatChainSingleton.chain = ChatChainSingleton.initialize_chain(new_model)
        return ChatChainSingleton.chain

    @staticmethod
    def get_model():
        return ChatChainSingleton.model

class CodeBot(Chatbot):
    def __init__(self, api_key, mongo_uri):
        logging.info("CodeBot initialized.")
        super().__init__(api_key, mongo_uri)
        self.chain = ChatChainSingleton().chain
        self.prompt = ChatChainSingleton().prompt

    def set_current_chat_id(self,user_id,chat_id):
        self.users_collection.update_one({"username":user_id},
                                         {"$set":{'current_chat_id_coderbot':chat_id}}
                                         )
        return chat_id
        
    def get_current_chat_id(self,user_id):
        #get currently selected chat from user, if none then generate one.
        user_doc = self.users_collection.find_one({'username':user_id})
        chat_id = user_doc.get('current_chat_id_coderbot')
        #if not found, create one.
        if not chat_id:
            new_chat_id = str(uuid.uuid4())
            chat_id = new_chat_id
            self.users_collection.update_one({"username":user_id},
                                                 {"$set":{'current_chat_id_coderbot':new_chat_id}}
                                                 )
        return chat_id
    
    def get_current_chat_history(self,user_id):
        chat_id = self.get_current_chat_id(user_id)
        user_doc = self.users_collection.find_one({'username':user_id})
        tutor_chat_histories = user_doc.get('coderbot_chat_histories')
        if not tutor_chat_histories:
            #create one and return original assistant prompt
            original_message = {"role":"assistant","content":"Hi! I am Coderbot, I will help you improve your prompts!"}
            self.users_collection.update_one({"username":user_id},
                                             {"$set":{"coderbot_chat_histories":{chat_id:{'timestamp':datetime.now().timestamp(),'chat_history': [original_message]}}}}
                                             )
            return [original_message]
        current_chat = tutor_chat_histories[chat_id]['chat_history']
        return current_chat
    
    def add_messages_to_chat_history(self,user_id,new_messages):
        chat_id = self.get_current_chat_id(user_id)
        chat_history_path = f'coderbot_chat_histories.{chat_id}.chat_history'
        chat_timestamp_path = f'coderbot_chat_histories.{chat_id}.timestamp'
        self.users_collection.update_one({'username':user_id},
                                         {'$push':{chat_history_path:{"$each":new_messages}}, #push is to push values into an existing object. Each is for pushing multiple values into that object
                                          '$set':{chat_timestamp_path: datetime.now().timestamp()}} # set is to update a specfic field in a object.
                                        ) 
        #in front end, it is added to the session state automatically
        return 'added successfully'
    def get_all_chat_ids(self,user_id):
        user_doc = self.users_collection.find_one({'username':user_id})
        chat_histories_object = user_doc.get('coderbot_chat_histories')
        chat_ids = chat_histories_object.keys()
        return list(chat_ids)
    
    def start_new_chat(self,user_id): 
        if st.session_state.selected_bot == "CodeBot":
                #This creates a new id for the code
                new_chat_id = str(uuid.uuid4())
                initial_message = {"role": "assistant", "content": "Hi! This is the start of a new CoderBot chat."}

            # Add the new chat to the database and set it as the current chat
                result = self.users_collection.update_one(
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
                
    def delete_chat(chatbot, user_id):
        if st.session_state.selected_bot == "CodeBot":

                """Delete the current chat from coderbot_chat_histories."""
            # Get the user's current chat ID
        user_doc = chatbot.users_collection.find_one({"username": user_id})
        current_chat_id = user_doc.get("current_chat_id_coderbot")
             # Delete the chat from the database
        result = chatbot.users_collection.update_one(
                    {"username": user_id},
                    {
                    "$unset": {f"coderbot_chat_histories.{current_chat_id}": ""},
                    "$set": {"current_chat_id_coderbot": None}  # Reset the current chat ID
                    }
                )
            # Clear session state messages
        st.session_state.messages = []
        logging.info(f"Chat with ID {current_chat_id} deleted successfully.")
        st.success("Chat deleted successfully!")

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

            formatted_prompt = self.prompt.format_prompt(**prompt_values)
            response = self.chain.invoke(prompt_values)
            assistant_message = response.content

            #add to DB
            new_messages = [{'role':'user','content':user_message},{'role':'assistant','content':assistant_message}]
            self.add_messages_to_chat_history(user_id,new_messages)
            logging.info("Response generated.")
            return assistant_message
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            return f"An error occurred: {e}"


