# Singleton class for LangChain ChatChain
import json
import logging
import streamlit as st
from typing import Any
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from components.Selectors import LoggingSemanticSimilarityExampleSelector
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
    MessagesPlaceholder,
)
import jsonlines 
import pandas as pd
import csv
import os
from components.system_prompt import system_prompts
from components.db_functions import get_bot_competions,get_bot_examples,get_course_id_from_course_name
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
        logging.info(f'Selected Bot :{st.session_state.selected_bot} ')
        #initial case, in case courses do not have any examples.
        few_shot_prompt = None   
        #use course id to find example file from mongo
        selected_bot_name = st.session_state.selected_bot
        selected_bot_id = get_course_id_from_course_name(selected_bot_name)
        examples = get_bot_examples(selected_bot_id)
        #if examples do not exist, use tutorbot examples
        if not examples:
            examples = get_bot_examples('tutorbot')
            
        try:
            embeddings = OpenAIEmbeddings(api_key=st.secrets['OPENAI_API_KEY'] )
            to_vectorize = ['.'.join(example.values()) for example in examples]
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

        #Assemble the final prompt template. If a system prompt exists use it, otherwise use tutorbot
        system_prompt = system_prompts[st.session_state.selected_bot] if st.session_state.selected_bot in system_prompts else system_prompts['tutorbot']
        prompt_messages = [("system", ( system_prompt ))]
        if few_shot_prompt:
            prompt_messages.append(few_shot_prompt.format())
        
        prompt_messages.extend([
             MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
        ])
        final_prompt = ChatPromptTemplate.from_messages(prompt_messages)

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