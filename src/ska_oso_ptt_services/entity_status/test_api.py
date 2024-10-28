import requests
import json

def read_file(path):
    with open(path, "r", encoding="utf-8") as json_file:
        return json.load(json_file)

# Read the JSON data from file
sbd_data = read_file("/home/sagar/Projects/ska-db-oda/tests/files/testfile_sample_mid_sb.json")

# Define the API endpoint URL
url = "http://0.0.0.0:8000/ska-db-oda/oda/api/v6/sbds"

# Set the headers
headers = {
    "Content-Type": "application/json"
}

# Make the POST request
response = requests.post(url, json=sbd_data, headers=headers)

# Check the response
if response.status_code == 200:
    print("SBD created successfully!")
    print(f"Created SBD ID: {response.json()}")
else:
    print("Failed to create SBD. Status code:", response.status_code)
    print("Response:", response.text)
