import pandas as pd
# import sys
import os
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# from src.online.memory import get_product_memory,set_product_memory
# from src.components.main import send_text
from offline.src.read_scripts import encod_chunks
import json
from typing import Union
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from qdrant_client import QdrantClient
# from pymongo import MongoClient
# import sys

# This ensures the directory containing 'bot.py' is in the search path
# --- Pydantic Schema for Validation ---
class IntentResponse(BaseModel):
    intent_id: int = Field(description="The numeric category of the intent")
    product_id: Union[str, int] = Field(default=0, description="The product ID or 0 if missing")
    order_id: Union[str, int] = Field(default=0, description="The order ID or 0 if missing")
    confidence_score: float = Field(default=1.0)

class OpenrouterClient:
    def __init__(self, api_key, base_url="https://openrouter.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url

    def chat_completion(self, response_type, temperature, model="nvidia/nemotron-3-nano-30b-a3b:free", messages=None):
        client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        
        # Build the payload
        payload = {
            "model": model,
            "messages": [{
                "role": "user",
                "content": messages,
            }],
            "temperature": temperature,
        }

        # ONLY add response_format if you actually want JSON
        if response_type == "json_object":
            payload["response_format"] = {"type": "json_object"}

        try:
            response = client.chat.completions.create(**payload)
            # This is where the 'NoneType' error usually happens if 'response' is empty
            if response and response.choices:
                return response.choices[0].message.content
            else:
                return "Error: Empty response from API"
        except Exception as e:
            return f"API Error: {str(e)}"
load_dotenv()
def intent_detection(query):
    load_dotenv()
    print(f"User Query: {query}")
    custom_api_key = os.getenv("CUSTOM_API_KEY")
    client = OpenrouterClient(custom_api_key)

    # Systematic Prompt for structural classification
    system_prompt = f"""
    Classify the user query into exactly one intent_id:
    1. See product with specific product_id, id starts with 'a'
    2. Place order with specific product_id, id starts with 'a'
    3. General query regarding policies (greetings, business info, human support)
    4. Track delivery status / Filing complaint
    5. Order/See product BUT product_id is MISSING (Intent 6/7 in your logic, simplified here)

    Rules:
    - You must return a JSON object with the following keys: "intent_id", "product_id", "order_id", and "confidence_score".
    - "intent_id" must be the integer (1-5) representing the classification.
    - If intent involves a product but NO product_id is found, set product_id to 0.
    - If intent involves an order but NO order_id is found, set order_id to 0.
    - "confidence_score" should be a float between 0 and 1.
    - Return ONLY valid JSON.
    Query: "{query}"
    """

    raw_response = client.chat_completion("json_object",0.0 ,messages=system_prompt)
    print(raw_response)
    try:
        # Step 1: Parse the string into JSON
        data = json.loads(raw_response)
        
        # Step 2: Validate with Pydantic
        validated_data = IntentResponse(**data)
        
        print(f"Validated JSON: {validated_data.model_dump()}")
        return validated_data.model_dump()
        
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"Error parsing LLM response: {e}")
        # Fallback to a safe 'General' classification
        return {"intent_id": 3, "product_id": 0, "order_id": 0}
uri=os.getenv('MONGO_URI')
mongo_client = MongoClient(uri, server_api=ServerApi('1'))
db=mongo_client["Spes-AI"]
products_collection=db["products"]
def see_prod(intent_dict):
    prod_id=intent_dict["product_id"]
    product = products_collection.find_one({"prod_id": prod_id})
    if product:
        product.pop('_id', None) # Clean up the response
    return product

def view_prod(product,indent=0):
    spacing = "  " * indent
    message=""
    for key, value in product.items():
        if isinstance(value, dict):
            # If the value is another dictionary, print the key and go deeper
            message = message+f"{spacing} {key.capitalize()}:\n"
            view_prod(value, indent + 1)
        elif isinstance(value, list):
             # Handle lists (like available_colors) gracefully
             message+=f"{spacing} {key.capitalize()}: {', '.join(map(str, value))}\n"
        else:
            # Print standard key-value pairs
            message+=f"{spacing} {key.capitalize()}: {value}\n"
    return message

order_collection=db["Orders"]
def order_prod(intent_dict):
    prod_id=intent_dict["product_id"]
    product=see_prod(intent_dict)
    message=view_prod(product)
    pass

def gen_query(user_text):
    qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"), 
    api_key=os.getenv("QDRANT_API_KEY"),
    )
    embed_query=encod_chunks(user_text,model_name="BAAI/bge-small-en-v1.5")
    print("embedding done")
    search_result = qdrant_client.query_points(
    collection_name="static-collection",
    query=embed_query,
    with_payload=True,
    limit=2
    ).points
    print(search_result)
    print("search done")
    # This version only includes the payload if it isn't None
    inputs = [item.payload for item in search_result if item.payload is not None]
    print(inputs)
    formatted_inputs = "\n".join([str(i) for i in inputs]) if inputs else "No information found."
    print(formatted_inputs)
    custom_api_key = os.getenv("CUSTOM_API_KEY")
    client2 = OpenrouterClient(custom_api_key)
    print("upto client 2 done")
    # Systematic Prompt for structural classification
    system_prompt = f"""Role: Info Assistant. Answer <query> using ONLY <inputs>.
        Constraints:
        - No outside info. If missing, say: "I'm sorry, I don't have information on that specific topic. Please contact our support team for further assistance."
        - No sales, pricing, or order status mentions.
        - Use neutral, objective tone. No fluff.
        Formatting:
        - Use bullet points for lists/steps.
        - **Bold** key terms and policies.
        - Synthesize multiple sections into one answer.
        <inputs>
        {inputs}
        </inputs>
        <query>
        {user_text}
        </query>
        """
    # system_prompt="how are you"
    response = client2.chat_completion(response_type="text",temperature=0.7,messages=system_prompt)
    print("response done")
    print(response)
    return response

def gen_prod_query(user_text):
    message="The query does not clearly mention the product id. i could not process the request. please mention the product id."
    return message

def track_status(intent_dict):
    pass

def process_message(user_text):
    intent_dict = intent_detection(user_text)
    if intent_dict["intent_id"]==1:
        product=see_prod(intent_dict)
        message=view_prod(product)
        return message
    
    elif intent_dict["intent_id"]==2:
        pass
        # product=see_prod(intent_dict)
        # order_prod(intent_dict)

    elif intent_dict["intent_id"]==3: #fully functioning upto here
        message=gen_query(user_text)
        return message

    elif intent_dict["intent_id"]==4:
        track_status(intent_dict)

    elif intent_dict["intent_id"]==5:
        return gen_prod_query(user_text)
    

def reply_to_user(user_text):
    message=process_message(user_text)
    return message
