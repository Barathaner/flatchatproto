# app.py
import time

from flask import Flask, request, jsonify
from pinecone import Pinecone, ServerlessSpec
import openairequests
from flask_cors import CORS  # Import CORS

import ast
import os

app = Flask(__name__)
CORS(app)  # Enable CORS on the entire app

def init_pinecone_db():
    index_name = "pcdb5"
    # Check if the index already exists
    pc = Pinecone()
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=1536,  # Replace with your model dimensions
            metric="dotproduct",  # Replace with your model metric
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )

    # connect to index
    index = pc.Index(index_name)
    return index

index= init_pinecone_db()


def preprocess_text(text):
    """ Normalize and clean text data. """
    text = text.lower()
    text = ''.join([c for c in text if c.isalnum() or c.isspace()])
    return text
def parse_conditions_to_pinecone_filters(input_string, min_lat=None, max_lat=None, min_lon=None, max_lon=None):
    if not input_string:  # Handle cases where the input string might be empty
        return {}

    conditions_dict = ast.literal_eval(input_string)
    condition_list = []

    # Process textual conditions from the input string
    for key, condition in conditions_dict.items():
        if key == 'numberofroommates':
            key = 'numberofroomates'
        if '==' in condition:
            _, value = condition.split('==')
            value = int(value.strip())
            # Adding a range around the exact value to allow for slight variations
            condition_list.append({key: {"$gte": value - 5, "$lte": value + 5}})
        elif '<=' in condition or '>=' in condition:
            parts = condition.split()
            if len(parts) == 5:
                lower_bound, _, _, _, upper_bound = parts
                condition_list.append({key: {"$gte": int(lower_bound)-1, "$lte": int(upper_bound)+1}})
            elif len(parts) == 3:
                operator, _, value = parts
                value = int(value)
                if operator == '<=':
                    condition_list.append({key: {"$lte": value+1}})
                elif operator == '>=':
                    condition_list.append({key: {"$gte": value-1}})

    # Add adjustments for geographic coordinate conditions if provided
    if min_lat is not None and max_lat is not None:
        condition_list.append({"latitude": {"$gte": float(min_lat) - 0.01, "$lte": float(max_lat) + 0.01}})
    if min_lon is not None and max_lon is not None:
        condition_list.append({"longitude": {"$gte": float(min_lon) - 0.01, "$lte": float(max_lon) + 0.01}})

    # Combine all conditions using $and logical operator
    return {"$and": condition_list} if condition_list else {}


def query_vector_db(prompt, num_results=30,min_lat=None,max_lat=None,min_lon=None,max_lon=None):
    preprocessed_prompt = preprocess_text(prompt)
    #print(f"Preprocessed Prompt: {preprocessed_prompt}")
    priceandroommates= openairequests.evaluate_prompt("give back only the price and number of roomates without any other words . if there is any price or number of roommmates mentioned then in format of a dictionary like this where the value is an interval condition like: {'price': 'price==1000', 'numberofroomates': '2 <= numberofroommates <=4'}, if there is no price or number of roommates mentioned then return None values for the missing value ." + preprocessed_prompt)
    #print(f"Price and Roommates: {priceandroommates}")

    priceandroommates = priceandroommates.strip("```python").strip()
    priceandroommates = priceandroommates.strip("```json").strip()
    conditions = parse_conditions_to_pinecone_filters(priceandroommates, float(min_lat), float(max_lat), float(min_lon), float(max_lon))
    print(f"Conditions: {conditions}")
    print(f"Prompt: {preprocessed_prompt}")
    embedding = openairequests.get_openai_embeddings(preprocessed_prompt)
    #print(f"Embedding: {embedding}")
    if embedding:
        #print(f"Query Embedding: {embedding[:5]}...")
        query_results = index.query(vector=[embedding], top_k=num_results,include_metadata=True, filter=conditions)
        #print(f"Query Results: {query_results}")
        return query_results.to_dict()
    else:
        print("Failed to generate embedding for the prompt.")
        return []


@app.route('/search_by_coordinates', methods=['POST'])
def search_by_coordinates():
    data = request.json
    min_lat = data['min_lat']
    max_lat = data['max_lat']
    min_lon = data['min_lon']
    max_lon = data['max_lon']
    print(data)
    # Constructing the filter for geographic coordinates
    filter_conditions = {
        "$and": [
            {"latitude": {"$gte": float(min_lat), "$lte": float(max_lat)}},
            {"longitude": {"$gte": float(min_lon), "$lte": float(max_lon)}}
        ]
    }

    # Query Pinecone without specifying a vector or ID
    results = index.query(vector=[0] * 1536,top_k=20, filter=filter_conditions, include_metadata=True)
    return jsonify(results.to_dict())


@app.route('/search_by_prompt', methods=['POST'])
def search_by_prompt():
    data = request.json
    prompt = data['prompt']
    min_lat = data['min_lat']
    max_lat = data['max_lat']
    min_lon = data['min_lon']
    max_lon = data['max_lon']

    print(f"Prompt: {prompt}", f"Min Lat: {min_lat}", f"Max Lat: {max_lat}", f"Min Lon: {min_lon}", f"Max Lon: {max_lon}")


    results = query_vector_db(prompt,5,min_lat,max_lat,min_lon,max_lon)
    #print(results)
    time.sleep(2)
    prompt+="These are the top 5 results, decide which one fits the description of the client the best, make sure to give back the id: \n"
    if results and 'matches' in results:
        for result in results['matches']:
            # Format and print each result
            caption = result['metadata']['caption']
            url = result['metadata']['url']
            prompt+= result["id"] + url +caption + "\n"

    #print(prompt)
    favorite = openairequests.evaluate_prompt(prompt)
    print(favorite)
    return jsonify(favorite)


if __name__ == '__main__':
    app.run(debug=True)
