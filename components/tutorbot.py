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
# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Custom selector with logging
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
        examples = [
            {
                "input": "What is a loop in Python?",
                "output": """
Are follow up questions needed here: Yes.
Follow up: Does this response do the assignment for you?
Intermediate answer: No.
Follow up: What is a loop in Python?
So the final answer is: In Python, a loop is a way to iterate over a sequence (like a list or tuple) or other iterable objects. The most common types of loops in Python are the 'for' loop and the 'while' loop. Would you like to see an example or review the concept of loops in more detail?
""",
            },
            {
                "input": "Write a function in Python that reverses a string.",
                "output": """
Are follow up questions needed here: Yes.
Follow up: Does this response do the assignment for you?
Intermediate answer: Yes.
Follow up: What concepts are needed to complete the following: Write a function in Python that reverses a string.
So the final answer is: Instead of providing a complete solution, let's review some concepts that will help you write the function: string manipulation in Python, writing functions in Python. Which concept would you like to start with?
""",
            },
            {
                "input": "I'm getting a error with this Python code: for i in range(10) print(i)",
                "output": """
Are follow up questions needed here: Yes.
Follow up: Does this response do the assignment for you?
Intermediate answer: No.
Follow up: I'm getting a error with this Python code: for i in range(10) print(i)
So the final answer is: It looks like you're missing a colon after the 'range(10)' in your 'for' loop. The correct syntax should be: for i in range(10): print(i). The colon is used to indicate the start of the loop's body. Would you like to review the syntax of 'for' loops in more detail?
""",
            },
            {
                "input": "What is polymorphism in Java?",
                "output": """
Are follow up questions needed here: Yes.
Follow up: Does this response do the assignment for you?
Intermediate answer: No.
Follow up: What is polymorphism in Java?
So the final answer is: Polymorphism in Java is the ability of an object to take on many forms. It allows one interface to be used for a general class of actions. The most common use of polymorphism in OOP is when a parent class reference is used to refer to a child class object. Would you like to explore an example of polymorphism or review the concept in more detail?
""",
            },
            {
                "input": "Can you solve this assignment for me? Write a function in Python that reverses a string.",
                "output": """
Are follow up questions needed here: Yes.
Follow up: Does this response do the assignment for you?
Intermediate answer: Yes.
Follow up: What concepts are needed to complete the following: Write a function in Python that reverses a string.
So the final answer is: Instead of providing a complete solution, let's review some concepts that will help you write the function: string manipulation in Python, writing functions in Python. Which concept would you like to start with?
""",
            },
            {
                "input": "My Python loop isn't working as expected. Can you help me debug it? for i in range(10): print(i)",
                "output": """
Are follow up questions needed here: Yes.
Follow up: Does this response do the assignment for you?
Intermediate answer: No.
Follow up: My Python loop isn't working as expected. Can you help me debug it? for i in range(10): print(i)
So the final answer is: It looks like your loop is syntactically correct, but if it's not working as expected, you might want to check the following: Ensure that the range is correct for the desired output. Check if there are any conditions or additional code inside the loop that could affect its behavior. You might want to review the concept of loops in Python and debugging techniques. Would you like to go over some debugging tips or review loops?
""",
            },
            {
                "input": "I'm getting a syntax error with this Python code: for i in range(10) print(i)",
                "output": """
Are follow up questions needed here: Yes.
Follow up: Does this response do the assignment for you?
Intermediate answer: No.
Follow up: I'm getting a syntax error with this Python code: for i in range(10) print(i)
So the final answer is: It looks like you're missing a colon after the 'range(10)' in your 'for' loop. The correct syntax should be: for i in range(10): print(i). The colon is used to indicate the start of the loop's body. Would you like to review the syntax of 'for' loops in more detail?
""",
            },
            {
                "input": "My function isn't returning the right result. def add(a, b): return a * b",
                "output": """
Are follow up questions needed here: Yes.
Follow up: Does this response do the assignment for you?
Intermediate answer: No.
Follow up: My function isn't returning the right result. def add(a, b): return a * b
So the final answer is: It seems like your function is multiplying 'a' and 'b' instead of adding them. To fix this, you should use the '+' operator instead of '*'. Here's the corrected function: def add(a, b): return a + b. You might want to review the concepts of functions and operators in Python. Would you like to go over these concepts?
""",
            },
            {
                "input": "I'm getting a 'NameError: name 'x' is not defined' in Python. What does this mean?",
                "output": """
Are follow up questions needed here: Yes.
Follow up: Does this response do the assignment for you?
Intermediate answer: No.
Follow up: I'm getting a 'NameError: name 'x' is not defined' in Python. What does this mean?
So the final answer is: A 'NameError' in Python indicates that the interpreter couldn't find a variable or function with the specified name. In this case, 'x' is not defined before it's being used. To fix this, you should ensure that 'x' is defined before using it, or check for typos in the variable name. Would you like to review variable scope and declaration in Python?
""",
            },
            {
                "input": "I need to write a Java method called 'triangle' that prints a pattern of asterisks, where the number of asterisks increases from m to n and then decreases back to m. How can I do this using recursion?",
                "output": """
Are follow up questions needed here: Yes.
Follow up: Does this response do the assignment for you?
Intermediate answer: Yes.
Follow up: What concepts are needed to complete the following: I need to write a Java method called 'triangle' that prints a pattern of asterisks, where the number of asterisks increases from m to n and then decreases back to m. How can I do this using recursion?
So the final answer is: It sounds like you're working on a recursive method in Java. To approach the 'triangle' method, consider how the pattern changes with each recursive call. You'll need a base case when m equals n, and for each recursive step, you can increase or decrease the number of asterisks. Think about how you can modify the parameters in the recursive call to reflect this pattern. Would you like to go over the concept of recursion and base cases in more detail?
""",
            },
            {
                "input": "I need to implement a recursive method in Java to print section numbers with a given prefix and levels. How should I approach this?",
                "output": """
Are follow up questions needed here: Yes.
Follow up: Does this response do the assignment for you?
Intermediate answer: Yes.
Follow up: What concepts are needed to complete the following: I need to implement a recursive method in Java to print section numbers with a given prefix and levels. How should I approach this?
So the final answer is: For the section numbers problem, you'll need to use recursion to generate the numbers with the specified levels. Consider how you can concatenate the prefix with the current level number and pass it to the next recursive call. You'll also need a base case to stop the recursion when you reach the desired level. Here's some pseudocode to get you started: public static void printSections(String prefix, int level) { if (level == 0) { System.out.println(prefix); return; } for (int i = 1; i <= 9; i++) { printSections(prefix + i + '.', level - 1); } }. This pseudocode outlines the structure of the recursive method. You'll need to adapt it to fit the specific requirements of your assignment. Would you like to review any concepts related to string manipulation or recursion?
""",
            },
            {
                "input": "How can I create a recursive function in Java to reverse a string?",
                "output": """
Are follow up questions needed here: Yes.
Follow up: Does this response do the assignment for you?
Intermediate answer: Yes.
Follow up: What concepts are needed to complete the following: How can I create a recursive function in Java to reverse a string?
So the final answer is: To create a recursive function for reversing a string in Java, you'll need to think about the base case and the recursive step. The base case could be when the string is empty or has a single character. For the recursive step, you can concatenate the last character of the string with the result of the recursive call on the substring excluding the last character. Here's some pseudocode to illustrate this: public static String reverseString(String str) { if (str.length() <= 1) { return str; } return str.charAt(str.length() - 1) + reverseString(str.substring(0, str.length() - 1)); }. This pseudocode provides a basic structure for the recursive function. You'll need to refine it and ensure it meets the requirements of your assignment. Would you like to go over the concepts of string manipulation and recursion in more detail?
""",
            },
            {
                "input": "I'm struggling with writing a recursive method to calculate the factorial of a number in Java. Any tips?",
                "output": """
Are follow up questions needed here: Yes.
Follow up: Does this response do the assignment for you?
Intermediate answer: Yes.
Follow up: What concepts are needed to complete the following: I'm struggling with writing a recursive method to calculate the factorial of a number in Java. Any tips?
So the final answer is: For writing a recursive method to calculate the factorial of a number in Java, you'll need to define a base case and a recursive case. The base case is usually when the number is 0 or 1, and the recursive case involves calling the method with the number minus one. Here's some pseudocode to help you get started: public static int factorial(int n) { if (n <= 1) { return 1; } return n * factorial(n - 1); }. This pseudocode outlines the basic structure of the recursive method. Remember to test your method with different input values to ensure it's working correctly. Would you like to review the concept of recursion or how to handle base cases in recursive methods?
""",
            },
        ]

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

        # Define the few-shot prompt template
        few_shot_prompt = FewShotChatMessagePromptTemplate(
            input_variables=["input"],
            example_selector=example_selector,
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
                few_shot_prompt.format(),
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

        # Create the chain with the final prompt and the chat model
        chain = final_prompt | chat_model

        # Store final_prompt and chain as class attributes
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

            formatted_prompt = self.prompt.format_prompt(**prompt_values)
            response = self.chain.invoke(prompt_values)
            assistant_message = response.content
            
            #add to DB, in main.py the messages get added to sessions state automatically
            new_messages = [{'role':'user','content':user_message},{'role':'assistant','content':assistant_message}]
            self.add_messages_to_chat_history(user_id,new_messages)

            logging.info("Response generated.")
            return assistant_message
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            return f"An error occurred: {e}"












































