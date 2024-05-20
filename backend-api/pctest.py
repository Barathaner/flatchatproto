import openairequests
from pinecone import Pinecone, ServerlessSpec
from pathlib import Path
import os
from utils import apply_function_to_folders
import pinecone
import nltk
from nltk.corpus import stopwords
import string
import pandas as pd
import os
import ast
import re

# Ensure the stopwords are downloaded
nltk.download('stopwords')
df = pd.read_csv("../data/rooms_cleaned_with_coordinates.csv")

stop_words = set(stopwords.words('english'))  # you can change 'english' to your target language

def parse_conditions_to_pinecone_filters(input_string):
    """
    Parse conditions from a string representation of a dictionary and convert them to Pinecone-compatible filters using $and/$or.

    Args:
    input_string (str): A string representation of a dictionary with conditions.

    Returns:
    dict: A dictionary where keys are the original dictionary's keys and values are Pinecone filter conditions using logical operators.
    """
    # Parse the input string to dictionary safely
    conditions_dict = ast.literal_eval(input_string)

    # Container for individual conditions
    condition_list = []

    # Iterate over items and convert conditions to Pinecone format with logical operators
    for key, condition in conditions_dict.items():
        single_condition = {}
        if '<=' in condition or '>=' in condition:
            parts = condition.split()
            if len(parts) == 5:  # Format: value1 <= key <= value2
                lower_bound, _, _, _, upper_bound = parts
                single_condition[key] = {"$gte": int(lower_bound), "$lte": int(upper_bound)}
            elif len(parts) == 3:  # Format: key <= value or key >= value
                operator, _, value = parts
                if operator == '<=':
                    single_condition[key] = {"$lte": int(value)}
                elif operator == '>=':
                    single_condition[key] = {"$gte": int(value)}
        elif '==' in condition:
            _, value = condition.split('==')
            single_condition[key] = {"$eq": int(value.strip())}

        if single_condition:
            condition_list.append(single_condition)

    # Combine all conditions with logical $and (if needed you can implement logic to decide when to use $and or $or)
    if len(condition_list) > 1:
        pinecone_filters = {"$and": condition_list}
    elif condition_list:
        pinecone_filters = condition_list[0]  # Only one condition, no need for $and
    else:
        pinecone_filters = {}

    return pinecone_filters



# Initialize Pinecone Index
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

# Function to add image to the vector database

def preprocess_text(text):
    """ Normalize, clean, and remove stopwords from text data. """
    # Convert to lowercase
    text = text.lower()
    # Remove punctuation
    text = ''.join([char for char in text if char not in string.punctuation])
    # Remove stopwords
    text = ' '.join([word for word in text.split() if word not in stop_words])
    # Remove non-alphanumeric characters (optional, already handled by removing punctuation)
    text = ''.join([char for char in text if char.isalnum() or char.isspace()])
    return text
def preprocess_text(text):
    """ Normalize and clean text data. """
    text = text.lower()
    text = ''.join([c for c in text if c.isalnum() or c.isspace()])
    return text

def extract_price(price_str):
    """ Extract numeric value from formatted price string. """
    # Find all numbers, ignore everything else
    numbers = re.findall(r'\d+', price_str.replace('€', ''))
    return int(numbers[-1]) if numbers else 0

def extract_number_of_roommates(roommates_str):
    """ Extract number of roommates from a descriptive string. """
    numbers = re.findall(r'\d+', roommates_str)
    return int(numbers[0]) if numbers else 0
def add_images_to_db(folder_path):
    # Gather all captions from the folder
    all_captions = []
    for image_filename in os.listdir(folder_path):
        image_path = os.path.join(folder_path, image_filename)
        if os.path.isfile(image_path):
            caption = openairequests.get_text_from_image(image_path)
            all_captions.append(preprocess_text(caption))  # preprocess each caption

    # Combine all captions into a single text block
    combined_caption = ' '.join(all_captions)

    # Generate a single embedding for the combined caption
    embedding = openairequests.get_openai_embeddings(combined_caption)

    # Use the folder name (ID) as the identifier for the embedding
    id = int(os.path.basename(folder_path))

    # Print combined caption and embedding snippet
    print(f"ID:{id}, Combined Caption: {combined_caption}, Embedding: {embedding[:5]}...")
    # Attempt to retrieve the price and number of roommates using the DataFrame
    try:
        price_series = df.loc[df['room_id'] == id, 'price']
        roommates_series = df.loc[df['room_id'] == id, 'subheading']

        # Convert the series to string if not empty
        price_str = price_series.iloc[0] if not price_series.empty else '0'
        roommates_str = roommates_series.iloc[0] if not roommates_series.empty else '0'
        latitude = df.loc[df['room_id'] == id, 'latitude'].iloc[0]
        longitude = df.loc[df['room_id'] == id, 'longitude'].iloc[0]
        print(latitude,longitude)
        print(f"Price: {price_str}, Roommates: {roommates_str}")
    except IndexError:
        print(f"No data found for ID {id}")
        price_str, roommates_str = 0, 0
        latitude,longitude=0,0

    metadata = {"caption": combined_caption, "url": folder_path, "price": int(price_str), "numberofroomates": int(roommates_str),"latitude":float(latitude),"longitude":float(longitude)}
    # Upsert the data into the database
    db.upsert(vectors=[(str(id), embedding, metadata)])

# Function to query the vector database and get top results
def query_vector_db(prompt, num_results=30):
    preprocessed_prompt = preprocess_text(prompt)
    priceandroommates= openairequests.evaluate_prompt("give back only the price and number of roomates without any other words . if there is any price or number of roommmates mentioned then in format of a dictionary like this where the value is an interval condition like: {'price': 'price==1000', 'numberofroomates': '2 <= numberofroommates <=4'}, if there is no price or number of roommates mentioned then return None values for the missing value ." + preprocessed_prompt)
    print(f"Price and Roommates: {priceandroommates}")
    conditions = parse_conditions_to_pinecone_filters(priceandroommates)
    print(f"Conditions: {conditions}")
    embedding = openairequests.get_openai_embeddings(preprocessed_prompt)
    if embedding:
        print(f"Query Embedding: {embedding[:5]}...")
        query_results = db.query(vector=[embedding], top_k=num_results,include_metadata=True,filter=conditions)
        print(f"Query Results: {query_results}")
        return query_results
    else:
        print("Failed to generate embedding for the prompt.")
        return []

if __name__ == "__main__":
    print("Initializing Pinecone DB...")
    db = init_pinecone_db()
    print("Populating Pinecone DB with image embeddings and offer ids...")
    #apply_function_to_folders("../pictures", add_images_to_db)
    print("Pinecone DB populated successfully.")
    print("Testing the Pinecone DB with a sample prompt...")
    testprompt = "I am searching a room with a wardrobe and sofa in the room and in the kitchen a dishwasher and a refrigerator and 3 buddies and between 100 and 2000 dollars."
    results = query_vector_db(testprompt,3)
    testprompt+="These are the top 3 results, decide which one fits the description of the client the best and contains the most details: \n"
    if results and 'matches' in results:
        for result in results['matches']:
            # Format and print each result
            caption = result['metadata']['caption']
            url = result['metadata']['url']
            testprompt+= result["id"] + url +caption + "\n"

    print(testprompt)
    favorite = openairequests.evaluate_prompt(testprompt)
    print(favorite)
