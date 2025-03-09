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
        # CSV reading, but need to convert to dict for metadata
        with open('components/examples.csv','r',newline='',encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            examples = [row for row in csv_reader]
        print(examples)

        #using jsonl would be most ideal to avoid converting dataframe to dict for metadata below but won't work
        #JSONL 1:
        # with jsonlines.open(f'components/examples/{st.session_state.selected_bot}.jsonl') as jsonl_f:
        #     try:
        #         examples = [obj for obj in jsonl_f]
        #     except json.decoder.JSONDecodeError as e:
        #         pass
        #JSONL 2: 
        # examples = []
        # with open(f'components/examples/{st.session_state.selected_bot}.jsonl','r',encoding='utf-8') as file:
        #     for line in file:
        #         json_obj = json.loads(line.strip())
        #         examples.append(json_obj)
        # print('printed examples!!')
        # print(examples)
        try:
            embeddings = OpenAIEmbeddings(api_key=st.secrets['OPENAI_API_KEY'] )
            to_vectorize = ['.'.join(example.values()) for example in examples]
            print(to_vectorize)
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