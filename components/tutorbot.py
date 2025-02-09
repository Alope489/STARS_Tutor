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
from datetime import datetime
import streamlit as st
import json
# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Custom selector with logging, custom class calls langchain semantic similarity class, all it does is logging.
#SemanticSimilarityExampleSelector class from langchain takes in 2 parameters, vectorstore and k. Select examples, takes input variable( user prompt) and then returns k most relevant examples.
class LoggingSemanticSimilarityExampleSelector(SemanticSimilarityExampleSelector):
    def select_examples(self, input_variables):
        selected_examples = super().select_examples(input_variables)
        logging.info("Few-shot examples selected.")
        return selected_examples

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
            examples = json.load(file)['tutorbot']

        # Create the vector store
        try:
            embeddings = OpenAIEmbeddings(api_key=st.secrets["OPENAI_API_KEY"])
            to_vectorize = [" ".join(example.values()) for example in examples]
            vectorstore = Chroma.from_texts(to_vectorize, embeddings, metadatas=examples, persist_directory=r"Documents")
            logging.info("Chroma initialized.")
        except Exception as e:
            logging.error(f"Chroma initialization failed: {e}")
            return None

        # Create the example selector
        example_selector = LoggingSemanticSimilarityExampleSelector(
            vectorstore=vectorstore, k=2
        )
        logging.info("Example selector initialized.")

        # Define the few-shot prompt template. This takes an example selector (containing vector store and k) as well 
        few_shot_prompt = FewShotChatMessagePromptTemplate(
          #states which variables are mandatory when writing the prompt
            input_variables=["input"],
            #contains vectorspace containing examples. When input given it finds the k most similar examples.
            example_selector=example_selector,
            #sets up a template format
            example_prompt=ChatPromptTemplate.from_messages(
                [("human", "{input}"), ("ai", "{output}")]
            ),
        )
        logging.info("Few-shot prompt template created.")

        # Assemble the final prompt template
        final_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "You are an advanced and interactive computer science tutor for college students. "
                        "Your primary goal is to help students understand programming concepts and problem-solving "
                        "techniques related to their coursework or assignments. You do this by: Guiding Exploration - "
                        "Encouraging students to think critically and uncover answers themselves through probing "
                        "questions, examples, and explanations of relevant concepts; Concept Clarification - Breaking "
                        "down technical topics, algorithms, and programming techniques into clear and accessible "
                        "explanations tailored to the students level of understanding; Debugging Assistance - Providing "
                        "step-by-step guidance to help students identify, understand, and fix issues in their code "
                        "without directly writing the solution for them this means if a prompt asks you to code something "
                        "you only give pseudocode; Promoting Independent Learning - Directing students to additional "
                        "resources, documentation, or reference materials to deepen their understanding. Restrictions: "
                        "Under no circumstances can you complete or solve the assignment, write the required code, or "
                        "provide the direct answer for the student. Instead, your role is to ensure the student gains the "
                        "knowledge and skills necessary to solve the problem independently. Format your answers in markdown, "
                        "and if you need to use code, put it in a code block with backticks like this: "
                        "```print(\"hello world!\")```. If you need to use equations, write them in LaTeX format, for example: "
                        "$$y = mx + b$$."
                    ),
                ),
    
                #UPDATE getting rid of .format() as it is not formatting anything
                #gives the most relevant examples here
                few_shot_prompt,
                #provided in generate_response when doing self.chain.invoke(formatted_prompt)
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )
        logging.info("Final prompt template assembled.")

        # Use OpenAI's GPT-4 model for the chat agent
        chat_model = ChatOpenAI(
            model=model,
            temperature=0.0,
            api_key=st.secrets["OPENAI_API_KEY"]
        )
        logging.info("Chat model initialized.")

        # Create the chain with the final prompt and the chat model. Equivalent to LLMChain(model=model,prompt=final_prompt)
        chain = final_prompt | chat_model

        # Store final_prompt and chain as class attributes to access elsewhere
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

# TutorBot class that inherits from Chatbot
class TutorBot(Chatbot):
    def __init__(self, api_key, mongo_uri):
        logging.info("TutorBot initialized.")
        super().__init__(api_key, mongo_uri)
        self.chain = ChatChainSingleton().chain
        self.prompt = ChatChainSingleton().prompt

    def set_current_chat_id(self,user_id,chat_id):
        self.users_collection.update_one({"username":user_id},
                                         {"$set":{'current_chat_id_tutorbot':chat_id}}
                                         )
        return chat_id
    def get_current_chat_id(self,user_id):
        #get currently selected chat from user, if none then generate one.
        user_doc = self.users_collection.find_one({'username':user_id})
        print(user_doc)
        chat_id = user_doc.get('current_chat_id_tutorbot')
        #if not found, create one.
        if not chat_id:
            new_chat_id = str(uuid.uuid4())
            chat_id = new_chat_id
            #this returns an update result object instead of the chat id
            self.users_collection.update_one({"username":user_id},
                                                 {"$set":{'current_chat_id_tutorbot':new_chat_id}}
                                        )
        return chat_id
    def get_current_chat_history(self,user_id):
        chat_id = self.get_current_chat_id(user_id)
        user_doc = self.users_collection.find_one({'username':user_id})
        tutor_chat_histories = user_doc.get('tutor_chat_histories')
        if not tutor_chat_histories:
            #create one and return original assistant prompt
            original_message = {"role":"assistant","content":"Hi! I am Tutorbot, ask me any question and I'll answer with specialized knowledge!"}
            self.users_collection.update_one({"username":user_id},
                                             {"$set":{"tutor_chat_histories":{chat_id:{'timestamp':datetime.now().timestamp(),'chat_history': [original_message]}}}}
                                             )
            return [original_message]
        current_chat = tutor_chat_histories[chat_id]['chat_history']
        return current_chat
    
    def add_messages_to_chat_history(self,user_id,new_messages):
        chat_id = self.get_current_chat_id(user_id)
        chat_history_path = f'tutor_chat_histories.{chat_id}.chat_history'
        chat_timestamp_path = f'tutor_chat_histories.{chat_id}.timestamp'
        
        self.users_collection.update_one({'username':user_id},
                                         {'$push':{chat_history_path:{"$each":new_messages}}, #push is to push values into an existing object. Each is for pushing multiple values into that object
                                          '$set':{chat_timestamp_path: datetime.now().timestamp()}} # set is to update a specfic field in a object.
                                         )
        #in front end, it is added to the session state automatically
        return 'added successfully'
    def get_all_chat_ids(self,user_id):
        user_doc = self.users_collection.find_one({'username':user_id})
        chat_histories_object = user_doc.get('tutor_chat_histories')
        chat_ids = chat_histories_object.keys()
        return list(chat_ids)
    def start_new_chat(self, user_id):     
            #This creates a new id for the code
            new_chat_id = str(uuid.uuid4())
            initial_message = {"role": "assistant", "content": "Hi! This is the start of a new TutorBot chat."}

            # Add the new chat to the database and set it as the current chat
            result = self.users_collection.update_one(
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
    def delete_chat(chatbot, user_id):
        """Delete the current chat from tutor_chat_histories."""
            # Get the user's current chat ID
        user_doc = chatbot.users_collection.find_one({"username": user_id})
        current_chat_id = user_doc.get("current_chat_id_tutorbot")
        # Delete the chat from the database
        result = chatbot.users_collection.update_one(
                {"username": user_id},
                    {
                        "$unset": {f"tutor_chat_histories.{current_chat_id}": ""},
                        "$set": {"current_chat_id_tutorbot": None}  # Reset the current chat ID
                    }
            )
        # Clear session state messages
        st.session_state.messages = []
        logging.info(f"Chat with ID {current_chat_id} deleted successfully.")
        st.success("Chat deleted successfully!")
           
              
        return

            
    def generate_response(self, user_id,messages):
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
            #here send to final_prompt which contains the system prompt, the few shot examples (k most relevant), and history
            formatted_prompt = self.prompt.format_prompt(**prompt_values)
            #here we invoke LLM using everything above
            response = self.chain.invoke(formatted_prompt)
            assistant_message = response.content
            
            #add to DB, in main.py the messages get added to sessions state automatically
            new_messages = [{'role':'user','content':user_message},{'role':'assistant','content':assistant_message}]
            self.add_messages_to_chat_history(user_id,new_messages)

            logging.info("Response generated.")
            return assistant_message
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            return f"An error occurred: {e}"












































