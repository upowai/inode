import os
from dotenv import load_dotenv

dotenv_path = ".env"
load_dotenv(dotenv_path)


class Env:
    def __init__(self):
        for key, value in os.environ.items():
            setattr(self, key, value)


env = Env()

b64_private_key = os.getenv("SHA_PRIVATE_KEY")
if b64_private_key is None:
    print(
        "SHA_PRIVATE_KEY not found. Please run 'python generatekey.py' to set the key in the .env variable."
    )
    exit(0)

Inode_private_key = os.getenv("PRIVATEKEY")
if Inode_private_key is None:
    print(
        "Inode PRIVATEKEY not found. Please check readme.md to set the PRIVATEKEY in the .env variable."
    )
    exit(1)

Inode_wallet_address = os.getenv("INODEWALLETADDRESS")
if Inode_wallet_address is None:
    print(
        "Inode INODEWALLETADDRESS not found. Please check readme.md to set the INODEWALLETADDRESS in the .env variable."
    )
    exit(2)

Inode_reward_address = os.getenv("INODEREWARDWALLETADDRESS")
if Inode_reward_address is None:
    print(
        "Inode INODEREWARDWALLETADDRESS not found. Please check readme.md to set the INODEREWARDWALLETADDRESS in the .env variable."
    )
    exit(3)

# Configuration settings
FETCH_VALIDATORS = "https://api.upow.ai/get_validators_info?inode=DbHgJVR7gDdTaxx7v3kX3GsxfJnTXy9zouSuzXE1TUWmB"
CORE_URL = "https://api.upow.ai"
INODE_IP = "0.0.0.0"
INODE_PORT = 65432
INODE_BUFFER = 1024

# Other configurations
INODE_WALLET_ADDRESS = env.INODEWALLETADDRESS
INODE_REWARD_WALLET_ADDRESS = env.INODEREWARDWALLETADDRESS
PRIVATEKEY = env.PRIVATEKEY
API_URL = "https://api.upow.ai"
FAST_API_URL = "0.0.0.0"
FAST_API_PORT = 8000
TRACK = 15616
