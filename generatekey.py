from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import base64
import os
from dotenv import load_dotenv, set_key


# Function to generate keys
def generate_keys():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    b64_private_key = base64.b64encode(pem).decode("utf-8")

    public_key = private_key.public_key()
    pub = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    b64_public_key = base64.b64encode(pub).decode("utf-8")

    return b64_private_key, b64_public_key


# Load existing .env file or create one if it doesn't exist
dotenv_path = ".env"
load_dotenv(dotenv_path)

# Check if keys already exist
existing_private_key = os.getenv("SHA_PRIVATE_KEY")
existing_public_key = os.getenv("SHA_PUBLIC_KEY")

if existing_private_key is None or existing_public_key is None:
    # Generate and set new keys if they don't exist
    b64_private_key, b64_public_key = generate_keys()
    set_key(dotenv_path, "SHA_PRIVATE_KEY", b64_private_key, quote_mode="never")
    set_key(dotenv_path, "SHA_PUBLIC_KEY", b64_public_key, quote_mode="never")
    print("New keys generated and saved.")
else:
    # Prompt user for action
    overwrite = input("Keys already exist. Overwrite? (y/n): ").strip().lower()
    if overwrite == "y":
        b64_private_key, b64_public_key = generate_keys()
        set_key(dotenv_path, "SHA_PRIVATE_KEY", b64_private_key, quote_mode="never")
        set_key(dotenv_path, "SHA_PUBLIC_KEY", b64_public_key, quote_mode="never")
        print("Keys overwritten and saved.")
    else:
        print("Operation cancelled. Existing keys are retained.")
