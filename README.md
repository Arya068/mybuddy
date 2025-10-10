# 🤗 MyBuddy - AI Mental Health Companion

This Streamlit application is **MyBuddy**, a compassionate AI-powered mental health companion designed to support students. In a world where academic and personal pressures can be overwhelming, MyBuddy offers a safe, non-judgmental space for users to express their feelings, receive empathetic support, and learn practical coping strategies.

## ✨ Features

- **Empathetic Chat**: Engage in supportive conversations with an AI companion powered by advanced language models like Llama 3.
- **Sentiment-Aware Responses**: The AI analyzes the user's mood to provide more appropriate and caring responses.
- **Crisis Support**: Detects signs of severe distress and provides immediate access to crisis hotlines and resources.
- **Relaxation & Coping Tools**: A built-in library of evidence-based techniques like Box Breathing, Grounding, and Progressive Muscle Relaxation.
- **Mood Tracker**: A simple tool for users to log and reflect on their emotional state over time.
- **Secure User Authentication**: A private and secure login system ensures that conversations remain confidential.
- **Personalized History**: Users can review their past conversations and mood check-ins to track their journey.
- **Secure & Private**: Leverages Streamlit's secrets management for API keys and database credentials, with user data stored securely in MongoDB.

## 🚀 Setup and Installation Guide

Follow these steps to get the application running on your local machine.

### Step 1: Get Your Credentials

You will need three things:
1.  **Hugging Face API Token**: To access the AI model.
2.  **MongoDB Connection URI**: To store user data and history.
3.  **Database and Collection Names**: To specify where to store the data in MongoDB.

*   **Hugging Face Token**:
    1.  Go to the Hugging Face website: huggingface.co
    2.  Navigate to **Settings** -> **Access Tokens** and create a new token with `read` permissions.
    3.  Copy the generated token (`hf_...`).

*   **MongoDB URI**:
    1.  Create a free cluster on MongoDB Atlas.
    2.  Once your cluster is set up, go to **Database** -> **Connect** -> **Drivers**.
    3.  Select Python and copy the connection string (URI). Remember to replace `<password>` with your database user's password.
    4.  You will also need to name your database and collection (e.g., `mybuddy_db`, `users`).

### Step 2: Create the Secrets File

Streamlit uses a `.streamlit/secrets.toml` file to store sensitive information like API keys.

1.  In your project's root directory (`mybuddy/`), create a new folder named `.streamlit`.
2.  Inside the `.streamlit` folder, create a new file named `secrets.toml`.
3.  Add your credentials to this file as shown below:

    ```toml
    # .streamlit/secrets.toml
    HF_TOKEN = "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    MONGO_URI = "mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority"
    DB_NAME = "your_database_name"
    COLLECTION_NAME = "your_collection_name"
    ```
    *Replace the placeholder values with your actual credentials.*

### Step 3: Install Dependencies

Open your terminal or command prompt, navigate to the project's root directory (`mybuddy/`), and run the following command to install the required Python packages:

```bash
pip install -r requirements.txt
```

### Step 4: Run the Streamlit App

Once the installation is complete, run the following command in your terminal:

```bash
streamlit run app.py
```

Your web browser should automatically open with the application running!

## 📁 Project Structure
mybuddy/
├── .streamlit/
│   └── secrets.toml
├── app.py
├── requirements.txt
└── README.md
