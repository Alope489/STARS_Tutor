from openai import OpenAI
import streamlit as st

client = OpenAI(api_key=st.secrets['OPENAI_API_KEY'])


def upload_training_file():
    file = client.files.create(
        file=open(f"components/{st.session_state.selected_bot}_completions.jsonl", "rb"),
        purpose="fine-tune"
    )
    return file.id

def create_fine_tuning_job(file_id):
    fine_tune_job = client.fine_tuning.jobs.create(
    training_file=file_id,
    model="gpt-4o-mini-2024-07-18:sandia-national-labs::BALUhqg9"
)
    return fine_tune_job

def perform_fine_tuning():
    file_id = upload_training_file()
    fine_tune_job = create_fine_tuning_job(file_id)
    return fine_tune_job

    

