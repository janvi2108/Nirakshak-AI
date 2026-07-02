import requests
import json

BASE_URL = "http://localhost:8080"

# Test health endpoint
print("Testing health endpoint...")
response = requests.get(f"{BASE_URL}/health")
print(f"Health: {response.status_code} - {response.json()}")

# Test register
print("\nTesting register endpoint...")
register_data = {
    "name": "Test User",
    "phone": "9876543210",
    "district": "Test District",
    "aadhaar_last4": "1234"
}
response = requests.post(f"{BASE_URL}/api/applications/register", json=register_data)
print(f"Register: {response.status_code}")
if response.status_code == 200:
    token_data = response.json()
    print(f"Token received: {token_data.get('access_token', 'N/A')[:20]}...")
    token = token_data.get('access_token')
    user_id = token_data.get('user_id')
    
    # Test create application
    print("\nTesting create application...")
    headers = {"Authorization": f"Bearer {token}"}
    app_data = {
        "cert_type": "caste_certificate",
        "citizen_name": "Test User",
        "citizen_phone": "9876543210",
        "district": "Test District",
        "aadhaar_last4": "1234"
    }
    response = requests.post(f"{BASE_URL}/api/applications/", json=app_data, headers=headers)
    print(f"Create app: {response.status_code}")
    if response.status_code == 201:
        app_id = response.json().get('id')
        print(f"Application created: {app_id}")
        
        # Test submit complaint
        print("\nTesting submit complaint...")
        complaint_data = {"text": "My certificate is delayed since 2 months"}
        response = requests.post(f"{BASE_URL}/api/complaints/", json=complaint_data, headers=headers)
        print(f"Submit complaint: {response.status_code}")
        if response.status_code == 201:
            print("✓ All tests passed!")
        else:
            print(f"Complaint error: {response.text}")
    else:
        print(f"Create app error: {response.text}")
else:
    print(f"Register error: {response.text}")