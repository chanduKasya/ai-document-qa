import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
api_key = os.getenv("LLM_API_KEY")
model_name = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")


client = Groq(api_key=api_key)

response = client.chat.completions.create(

    model = model_name,
    messages = [{"role": "user", "content": "Hello, how are you?"}]

)

print(response.choices[0].message.content)

