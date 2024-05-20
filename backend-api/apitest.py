import requests
import json

def test_search_by_coordinates(base_url):
    url = f"{base_url}/search_by_coordinates"
    payload = {
        "min_lat": 41.0,
        "max_lat": 42.0,
        "min_lon": 2.0,
        "max_lon": 3.0
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print("Response from search_by_coordinates:")
    print(response.text)

def test_search_by_prompt(base_url):
    testprompt = "I am searching a room with a wardrobe and sofa in the room and in the kitchen a dishwasher and a refrigerator and 3 buddies and between 100 and 2000 dollars."

    url = f"{base_url}/search_by_prompt"
    payload = {
        "prompt": testprompt,
        "min_lat": 41,
        "max_lat": 42.400,
        "min_lon": 2.150,
        "max_lon": 3.190
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print("Response from search_by_prompt:")
    print(response.text)

if __name__ == "__main__":
    base_url = "http://localhost:5000"  # Adjust this as necessary
    #test_search_by_coordinates(base_url)
    test_search_by_prompt(base_url)
