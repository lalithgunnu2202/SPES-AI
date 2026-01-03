from openai import OpenAI
import os
from dotenv import load_dotenv
import json
import pprint
from src.components.online import run
import pandas as pd
# from src.components.main import send_text

class OpenrouterClient:
    def __init__(self,api_key, base_url="https://openrouter.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        # self.header={
        #     "Authorization":f"bearer {api_key}",
        #     "content-type":"application/json"
        # }

    def chat_completion(self,model="nvidia/nemotron-nano-12b-v2-vl:free", messages=None,temperature=0.7):
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

def intent_detection(query):
    load_dotenv()
    print(f"user query:{query}")
    custom_api_key = os.getenv("CUSTOM_API_KEY")
    client = OpenrouterClient(custom_api_key)
    response = client.chat_completion(messages=f"for the given query: {query} classify it into one of the following intents.      1. trying to order product with specific numeric id, 2. Human Support request, 3. trying to see product with specific numeric id, 4. any other general question 5. if it a complaint regarding purchased product. return the number corresponding to intent only. do not return any other things. do not give \n also" )
    print(response)
    return response

def prepare_message(message):
    load_dotenv()
    # send_text(query)
    # print(f"user query:{query}")
    # data = run(query)
    custom_api_key = os.getenv("CUSTOM_API_KEY")
    client = OpenrouterClient(custom_api_key)
    response = client.chat_completion(messages=message )
    print(response)
    return response

def gen_ques(query):
    data = run(query)
    reply = prepare_message(f"assume you are a chatbot for ecommerce brand, be polite. answer only using the given data: {data} give useful oneliner or give neccessary answer if neccessary for the query: {query}")
    return reply

def ord_spec_id(query):
    load_dotenv()
    custom_api_key = os.getenv("CUSTOM_API_KEY")
    client = OpenrouterClient(custom_api_key)
    response = client.chat_completion(messages=f"from this query: {query} extract the product id. return the id only. do not return any other things." )
    df = pd.read_excel("/content/drive/MyDrive/SPES AI/SPES AI v1/data_srcs/products/products.xlsx")
    print(response.split())
    df["Product_ID"] = df["Product_ID"].astype(int)
    product  = df[df["Product_ID"]==int(response)]
    data = product.to_dict(orient="records")[0]
    print(data)
    reply = prepare_message(f"assume you are a chatbot for ecommerce brand, be polite. answer only using the given data: {data}. give the whole data as a product card for customers. highlight the price of the product. and inform them <this product is being ordered and thank you for shopping with us. our executive will contact you and will collect the payment>")
    return reply

def see_spec_id(query):
    load_dotenv()
    custom_api_key = os.getenv("CUSTOM_API_KEY")
    client = OpenrouterClient(custom_api_key)
    response = client.chat_completion(messages=f"from this query: {query} extract the product id. return the id only. do not return any other things." )
    df = pd.read_excel("/content/drive/MyDrive/SPES AI/SPES AI v1/data_srcs/products/products.xlsx")
    print(response.split())
    df["Product_ID"] = df["Product_ID"].astype(int)
    product  = df[df["Product_ID"]==int(response)]
    data = product.to_dict(orient="records")[0]
    reply = prepare_message(f"assume you are a chatbot for ecommerce brand, be polite. answer only using the given data: {data}. give the whole data as a product card for customers. highlight the price of the product. and ask them to buy this product")
    return reply

def hum_rep(query):
    reply = prepare_message(f"assume you are a chatbot for ecommerce brand, be polite. give this reply: <Talk to our representative regarding the {query} on call: 7893867545. we are always ready to solve your queries>")
    return reply

def complaint(query):
    with open("/content/drive/MyDrive/SPES AI/SPES AI v1/data_srcs/complaints/complaints.txt", "a") as f:
        f.write(f"{query} \n\n")
    reply = prepare_message("aassume you are a chatbot for ecommerce brand, be polite.dont write mail formats. give reply as a message. give this reply: your complaint has been noted. we will try our best to resolve the issue. our executive will contact you within next 24 hrs. reply should be under 20 words.")
    return reply

def reply_to_user(query):
    intent = int(intent_detection(query))
    if intent==1:
        reply = ord_spec_id(query)
        return reply
    if intent==2:
        reply = hum_rep(query)
        return reply
    if intent==3:
        reply = see_spec_id(query)
        return reply
    if intent==4:
        reply = gen_ques(query)
        return reply
    if intent==5:
        reply = complaint(query)
        return reply
