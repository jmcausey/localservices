import requests
import os

def f():
    # Replace with your actual API key or use "DEMO_KEY" for limited testing
    API_KEY = os.getenv('NASA_API_KEY')
    url = f"https://api.nasa.gov/planetary/apod?api_key={API_KEY}"

    response = requests.get(url)
    data = response.json()
    print(data)

f()

#print(f"Title: {data['title']}")
#print(f"Date: {data['date']}")
#print(f"Explanation: {data['explanation']}")
#print(f"Image URL: {data['url']}")
