from openai import OpenAI
import streamlit as st
import logging
import jsonlines 
from pymongo import MongoClient
import json 
from components.system_prompt import system_prompts
from groq import Groq
from dotenv import load_dotenv
import streamlit as st
import os
load_dotenv()

client = MongoClient("mongodb://localhost:27017/")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

db = client["user_data"]
users_collection = db["users"]
archive = client["chat_app"]
chats_collection = archive["chats"]
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))


openai_client = OpenAI(api_key=st.secrets['OPENAI_API_KEY'])


def upload_training_file():
    file = openai_client.files.create(
        file=open(f"components/completions/{st.session_state.selected_bot}_completions.jsonl", "rb"),
        purpose="fine-tune"
    )
    return file.id

def create_fine_tuning_job(file_id):
    fine_tune_job = openai_client.fine_tuning.jobs.create(
    training_file=file_id,
    model="gpt-4o-mini-2024-07-18"
)
    return fine_tune_job

def perform_fine_tuning():
    file_id = upload_training_file()
    fine_tune_job = create_fine_tuning_job(file_id)
    return fine_tune_job

def set_current_completion(completion):
    st.session_state.selected_completion = completion

def add_examples(selected_bot,input,output):
    #input is the user question. Output is the questions plus user answers
    new_entry = {'input':input,'output':output}
    with jsonlines.open(f'components/examples/{selected_bot}.jsonl','a') as writer:
        writer.write(new_entry)
    

def add_completions(selected_bot,prompt,answer):
    system_prompt = system_prompts[st.session_state.selected_bot]
        
    completion = {"messages":[{"role":"system","content":system_prompt},{"role":"user","content":prompt},{"role":"assistant","content":answer}]}
    with jsonlines.open(f"components/completions/{selected_bot}_completions.jsonl",'a') as writer:
        writer.write(completion)
    perform_fine_tuning()

def validate_final_answer(user_question,final_answer):
    system_prompt = system_prompts['tutorbot']
    validation_prompt = f"""You will fine tune responses for this AI model. You wil be given a user question and an assistant's answer as well the model's system prompt. 
    Based on the answer you return True or False whether it:
    1) Does it Answers Question Fully
    2) Does it Stay within domain of subject
    3) Does it explain the underlying concepts and help guide the student to the solution through their own efforts, or does it provide a direct solution that does not require effort on the students behalf?

    User question: {user_question}
    Assistant Response : {final_answer}

    System Prompt for this model : {system_prompt}

     You must answer in this json format :
     {{
     "result" : true
     }}
       """
    completion = groq_client.chat.completions.create(
        model="DeepSeek-R1-Distill-Llama-70b",
        messages=[{"role":"system","content":validation_prompt}],
        response_format={"type":"json_object"}
    )
    return json.loads(completion.choices[0].message.content)['result']
    
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
                #Form for uploading examples and completions
                with st.form('my_form'):
                    follow_up_question_needed = st.selectbox('Are Follow up questions needed here?',('Yes','No'),index=None,placeholder='Yes/No')
                    code_accuracy = st.selectbox('How accurately does the generated code perform the task?',('Failure','Slightly','Moderately','Highly'),index=None,placeholder='Select Accuracy')
                    requirements_fufilled = st.selectbox('Does the generated code fulfill the requirements?',('Yes','No'),index=None,placeholder='Yes/No')
                    final_answer = st.text_area('Preferred Answer: ')

                    filled_in = all([follow_up_question_needed,code_accuracy,requirements_fufilled,final_answer])
                    example = f"""Are Follow up questions needed here? {follow_up_question_needed}.How accurately does the generated code perform the task? : It {code_accuracy} performs the task
                        Does the generated code fulfill the requirements? : {requirements_fufilled}. Final Answer : {final_answer}
                    """
                    submit = st.form_submit_button("Submit")
                    if submit:
                        if filled_in:
                            is_valid = validate_final_answer(selected_completion['Question'],final_answer)                                
                            if is_valid:
                                add_examples(st.session_state.selected_bot,selected_completion['Question'],example)
                                add_completions(st.session_state.selected_bot,selected_completion['Question'],final_answer)
                                st.success('Created Few shot prompt and completion for training!')

                            else:
                                st.error('Your answer is either incorrect, not answering the question fully, or is not conducive to student learning, Try again!')
                        else:
                            st.error('You must fill in the answers')
                    
