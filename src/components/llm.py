from openai import OpenAI
import os
from dotenv import load_dotenv
import json
import pprint
from src.components.online import run
from src.components.main import send_text

class OpenrouterClient:
    def __init__(self,api_key, base_url="https://openrouter.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        # self.header={
        #     "Authorization":f"bearer {api_key}",
        #     "content-type":"application/json"
        # }

    def chat_completion(self,model="openai/gpt-oss-20b:free", messages=None,temperature=0.7):
        client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        response = client.chat.completions.create(
            model=model,
            messages=[{
                "role":"user",
                "content":messages,
            }],
            temperature=temperature
        )
        matter = response.choices[0].message.content
        return matter

def prepare_message(query):
    load_dotenv()
    send_text(query)
    print(f"user query:{query}")
    data = run()
    custom_api_key = os.getenv("CUSTOM_API_KEY")
    client = OpenrouterClient(custom_api_key)
    response = client.chat_completion(messages=f"assume you are a chatbot for ecommerce brand, be polite. answer only using the given data: {data} give useful oneliner or give full answer if neccessary for the query: {query}" )
    print(response)
    return response