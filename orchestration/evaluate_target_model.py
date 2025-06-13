import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_KEY")
client = OpenAI(api_key=OPENAI_KEY)

def model_attempts_answer(problem_text):
    """Call the target model (o1) to attempt solving the problem."""
    messages = [
        {"role": "system", "content": "You are a math student trying to solve the following problem. Only provide the final answer. No explanation."},
        {"role": "user", "content": problem_text}
    ]

    response = client.chat.completions.create(
        model="o1",
        messages=messages,
        temperature=1.0
    )

    return response.choices[0].message.content.strip()