'''
Adding OpenAI's ChatGPT to allow
users to gain recommendations for
their personal finances.
'''
# Adding local imports
# pip install python-dotenv flask openai
import openai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set API key for OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to get AI's response
# Assumes user_message is a string input
def get_user_response(user_message):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        max_tokens=150,
        temperature=0.5,
        messages=[
            {"role": "system", "content": "You are an AI tutor specializing in computer science. Your task is to provide detailed, clear, and accurate explanations to help students understand complex concepts and interview guidance. Your responses should be tailored to the user's current level of knowledge and aim to clarify difficult topics effectively."},
            {"role": "user", "content": user_message}
        ]
    )
    return response.choices[0].message['content']
