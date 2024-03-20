from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import requests
import os
import base64
from dotenv import load_dotenv

# Load .env file
dotenv_path = ".env"
load_dotenv(dotenv_path)


def load_public_key():
    b64_public_key = os.getenv("SHA_PUBLIC_KEY")
    if b64_public_key is None:
        print(
            "SHA_PUBLIC_KEY not found. Please run 'python generatekey.py' to set the key in the .env variable."
        )
        exit(1)  # Exit the script with an error code indicating failure
    pem_public_key = base64.b64decode(b64_public_key)
    return serialization.load_pem_public_key(pem_public_key)


def encrypt_message(public_key, message):
    try:
        return public_key.encrypt(
            message.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
    except Exception as e:
        print(f"Error encrypting message: {e}")
        exit(1)


def send_request(encrypted_message):
    try:
        response = requests.post(
            "http://localhost:8000/modify-pool-list/", data=encrypted_message
        )
        response.raise_for_status()  # This will raise an exception for HTTP error codes
        return response.json()
    except (
        requests.RequestException
    ) as e:  # This catches HTTP errors and other Request issues
        print(f"Request failed: {e}")
        exit(1)


public_key = load_public_key()

# Encrypt the message
encrypted_message = encrypt_message(
    public_key, "add:DhWyMUj2pna2UYbvrqULyLf6dEo2MNzPHA7Uh4kBrJGFY"
)

# Send the request and print the response
response = send_request(encrypted_message)
print(response)
