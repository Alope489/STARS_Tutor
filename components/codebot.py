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
        examples = [
            {
                "input": "User's code: def reverse_string(s): return s[::-1]",
                "output": """
    Are follow up questions needed here: Yes.
    Follow up: How close is the student's response?
    Intermediate answer: The student's code correctly implements a function that reverses a string using slicing.
    Follow up: Does the code meet the requirements and follow best practices?
    So the final answer is: The student's code effectively reverses the input string using Python's slicing syntax. It meets the requirements and follows best practices for string manipulation in Python.
    """,
            },
            {
                "input": "Prompt: Write a Python function that checks if a number is prime.",
                "output": """
    Are follow up questions needed here: Yes.
    Follow up: How accurately does the generated code fulfill the task?
    Intermediate answer: The generated code correctly defines a function to check for prime numbers but may not handle edge cases.
    Follow up: Does the code accurately determine if a number is prime for all cases?
    So the final answer is: The code provides a basic implementation for checking prime numbers but fails for inputs less than 2 and even numbers greater than 2. Refinements are needed to handle these cases and improve efficiency.
    """,
            },
            {
                "input": "User's code: def factorial(n): return n * factorial(n-1)",
                "output": """
    Are follow up questions needed here: Yes.
    Follow up: How close is the student's response?
    Intermediate answer: The student attempted to write a recursive factorial function but did not include a base case.
    Follow up: What corrections are needed in the student's code?
    So the final answer is: The student's code lacks a base case, which will lead to a recursion error. Adding a base case like 'if n <= 1: return 1' will fix the issue. The corrected function is:

    def factorial(n):
        if n <= 1:
            return 1
        return n * factorial(n-1)
    """,
            },
            {
                "input": "Prompt: Generate code to read a file and print its contents line by line in Python.",
                "output": """
    Are follow up questions needed here: Yes.
    Follow up: How accurately does the generated code fulfill the task?
    Intermediate answer: The generated code correctly opens a file and prints each line, handling file operations properly.
    Follow up: Does the code handle potential exceptions or errors?
    So the final answer is: The code successfully reads and prints the file contents line by line. However, it could be improved by adding exception handling to manage cases where the file might not exist. Including a 'try-except' block would enhance its robustness.
    """,
            },
            {
                "input": "User's code: def sum_list(lst): total = 0 for num in lst: total += num return total",
                "output": """
    Are follow up questions needed here: Yes.
    Follow up: How close is the student's response?
    Intermediate answer: The student's code correctly sums the elements of a list and returns the total.
    Follow up: Does the code follow best practices and handle edge cases?
    So the final answer is: The student's code accurately calculates the sum of a list of numbers. It follows best practices and should handle lists of any length, including empty lists, where it correctly returns 0.
    """,
            },
            {
                "input": "Prompt: Write a Python function to sort a list of numbers in ascending order without using built-in sort functions.",
                "output": """
    Are follow up questions needed here: Yes.
    Follow up: How accurately does the generated code perform the task?
    Intermediate answer: The generated code implements a basic sorting algorithm like bubble sort to sort the list.
    Follow up: Is the code efficient and does it avoid using built-in sort functions?
    So the final answer is: The code correctly sorts a list in ascending order without using built-in functions, meeting the requirements. While bubble sort is not the most efficient algorithm for large lists, it satisfies the task's constraints.
    """,
            },
            {
                "input": "User's code: def fibonacci(n): a, b = 0, 1 for _ in range(n): a, b = b, a + b return a",
                "output": """
    Are follow up questions needed here: Yes.
    Follow up: How close is the student's response?
    Intermediate answer: The student's code aims to compute the nth Fibonacci number but returns incorrect values due to loop range.
    Follow up: What corrections are needed in the student's code?
    So the final answer is: The code has an off-by-one error in the loop range. Adjusting the range to 'range(n)' or 'range(n-1)' depending on the definition will fix the issue. The corrected code will accurately compute the nth Fibonacci number.
    """,
            },
            {
                "input": "Prompt: Create a Python class called 'Circle' with a method to compute the area given the radius.",
                "output": """
    Are follow up questions needed here: Yes.
    Follow up: Does the generated code fulfill the requirements?
    Intermediate answer: The generated code defines a 'Circle' class with an '__init__' method and an 'area' method that calculates the area.
    Follow up: Are there any improvements or corrections needed?
    So the final answer is: The code meets the requirements by defining the 'Circle' class and computing the area correctly using the formula πr². To enhance the code, importing the 'math' module for the value of π is recommended. Here's the improved code:

    import math

    class Circle:
        def __init__(self, radius):
            self.radius = radius

        def area(self):
            return math.pi * self.radius ** 2
    """,
            },
            {
                "input": "User's code: for i in range(5): print('Hello World')",
                "output": """
    Are follow up questions needed here: Yes.
    Follow up: How close is the student's response to printing 'Hello World' five times?
    Intermediate answer: The student's code correctly prints 'Hello World' five times using a for loop.
    Follow up: Does the code follow best practices?
    So the final answer is: The student's code is correct and efficient. It uses a for loop to print 'Hello World' five times, meeting the task requirements.
    """,
            },
            {
                "input": "Prompt: Generate Python code to find the maximum number in a list.",
                "output": """
    Are follow up questions needed here: Yes.
    Follow up: How accurately does the generated code perform the task?
    Intermediate answer: The generated code iterates through the list to find the maximum value without using built-in functions.
    Follow up: Is the code efficient and does it handle edge cases?
    So the final answer is: The code correctly finds the maximum number by iterating through the list. It handles empty lists by initializing the maximum value appropriately. While using built-in functions like 'max()' is more concise, the code meets the requirement of not using them.
    """,
            },
        ]

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


