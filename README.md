# Set Up Environment and Download Dependencies

**Clone the Repo**
git clone https://github.com/Stars-AI-tutor/STARS_Tutor.git

1. **Create Virtual Environment:**
    - Run the following command:
      ```bash
      python3 -m venv venv
      ```

2. **Activate Virtual Environment:**
    - **Mac/Linux:**
      ```bash
      source venv/bin/activate
      ```
    - **Windows:**
      ```bash
      venv\Scripts\activate
      ```

3. **Install Dependencies:**
    - Run the following command:
      ```bash
      pip install -r requirements.txt
      ```

4. **Set Up Environment Variables:**
    - Create a `.streamlit` folder in the root directory, followed by a secrets.toml inside the folder .
    - Add the following variables:
      ```
      OPENAI_API_KEY=your OpenAI API key
      GROQ_API_KEY=your Groq API key
      BREVO_API_KEY = your Brevo API key
      MONGO_URI = your atlas mongo uri when deployed. mongodb://localhost:27017 when deployed     
      ```

# MongoDB Setup

1. **Download MongoDB Compass (GUI):**
    - [Download MongoDB Compass](https://www.mongodb.com/try/download/compass)

2. **Create New Connection in Compass:**
    - Under the new connection, create 3 databases `user_data`, `chat_app`, and `model_data`.
    - Inside `user_data`, create the following collections:  `users`, `tokens`, `courses`
    - Inside `chat_app` create `chats` collection
    - Inside `model_data` create `completions`, `examples`, `model_names`, `system_prompts`
    - Add Admin Test User :
    - - Once deployed you would add Professor Malik and Gilal
      ```json
      {
  "_id": "67f96897463b61af9e061796",
  "fname": "Test",
  "lname": "Admin",
  "email": "tadmin@fiu.edu",
  "user_type": "admin",
  "password": "af87163f8788dca36b0a26ad2912e3df0c38079da34616b61821a839a7baa0ff",
  "salt": "fd8297b5a4ff28bdf3cf0d5085842306"
}



# Feature Branch Workflow

1. **Create a New Branch:**
    - Run the following command:
      ```bash
      git checkout -b feature-branch-name
      ```

2. **Make Changes to the Code:**
    - Edit your code as needed.

3. **Commit the Changes:**
    - Run the following command:
      ```bash
      git commit -m "commit message"
      ```

4. **Push the Changes:**
    - Run the following command:
      ```bash
      git push origin feature-branch-name
      ```

5. **Create a Pull Request:**
    - Open your repository on GitHub and create a pull request for your feature branch.
