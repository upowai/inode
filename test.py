from dotenv import load_dotenv
import os

# Load environment variables from a .env file
load_dotenv()

b64_private_key = os.getenv("PRIVATE_KEY")

print(b64_private_key)
