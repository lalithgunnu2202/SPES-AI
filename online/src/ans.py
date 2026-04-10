import pandas as pd
# from src.online.memory import get_product_memory,set_product_memory
# from src.components.main import send_text
from offline.src.read_scripts import encod_chunks
import os
import json
from typing import Union
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError
from pymongo import MongoClient
# from pymongo import MongoClient

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

    def chat_completion(self, model="nvidia/nemotron-nano-12b-v2-vl:free", messages=None, temperature=0.0):
        client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        # temperature is set to 0.0 for deterministic JSON output
        response = client.chat.completions.create(
            model=model,
            messages=[{
                "role": "user",
                "content": messages,
            }],
            temperature=temperature,
            response_format={"type": "json_object"} # Hints model to output JSON
        )
        matter = response.choices[0].message.content
        return matter
load_dotenv()
def intent_detection(query):
    load_dotenv()
    print(f"User Query: {query}")
    custom_api_key = os.getenv("CUSTOM_API_KEY")
    client = OpenrouterClient(custom_api_key)

    # Systematic Prompt for structural classification
    system_prompt = f"""
    Classify the user query into exactly one intent_id:
    1. See product with specific product_id
    2. Place order with specific product_id
    3. General query (greetings, business info, human support)
    4. Track delivery status / Filing complaint
    5. Order/See product BUT product_id is MISSING (Intent 6/7 in your logic, simplified here)

    Rules:
    - If intent involves a product but NO product_id is found, set product_id to 0.
    - If intent involves an order but NO order_id is found, set order_id to 0.
    - Return ONLY a JSON object.

    Query: "{query}"
    """

    raw_response = client.chat_completion(messages=system_prompt, temperature=0.0)
    
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
client = MongoClient(uri, server_api=ServerApi('1'))
db=client["Spes-AI"]
products_collection=db["products"]
def see_prod(intent_dict):
    prod_id=intent_dict["product_id"]
    product = products_collection.find_one({"product_id": prod_id})
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
    embed_query=encod_chunks(user_text,model_name="BAAI/bge-small-en-v1.5")
    search_result = client.query_points(
    collection_name="static-collection",
    query=embed_query,
    with_payload=True,
    limit=3
    ).points
    inputs = [item["payload"] for item in search_result]

    custom_api_key = os.getenv("CUSTOM_API_KEY")
    client = OpenrouterClient(custom_api_key)

    # Systematic Prompt for structural classification
    system_prompt = f"""### Role
        You are a specialized Information Assistant for [Brand Name]. Your sole purpose is to answer customer questions accurately using the provided reference material.

        ### Strict Constraints
        1. **Source Fidelity:** Answer the <query> using ONLY the information contained within the <inputs>. 
        2. **The "I Don't Know" Rule:** If the answer is not explicitly stated in the <inputs>, do not use outside knowledge. Instead, respond with: "I'm sorry, I don't have information on that specific topic. Please contact our support team for further assistance."
        3. **No Sales/Orders:** Do not mention purchasing, viewing products, or order status. Focus entirely on answering the informational query.
        4. **Objectivity:** Maintain a neutral, helpful, and direct tone. Avoid marketing fluff or promotional language.

        ### Formatting
        - Use bullet points for steps or lists of information.
        - Use **bolding** for key terms, deadlines, or policy names.
        - If the <inputs> contain multiple sections, synthesize them into one cohesive answer.

        ### Reference Content
        <inputs>
        {inputs}
        </inputs>

        ### User Query
        <query>
        {user_text}
        </query>

        ### Answer
        """
    response = client.chat_completion(messages=system_prompt, temperature=0.7)
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
        product=see_prod(intent_dict)
        order_prod(intent_dict)

    elif intent_dict["intent_id"]==3:
        message=gen_query(user_text)
        return message

    elif intent_dict["intent_id"]==4:
        track_status(intent_dict)

    elif intent_dict["intent_id"]==5:
        return gen_prod_query(user_text)
    

def reply_to_user(user_text):
    message=process_message(user_text)
