import os
from dotenv import load_dotenv

dotenv_path = ".env"
load_dotenv(dotenv_path)


class Env:
    def __init__(self):
        for key, value in os.environ.items():
            setattr(self, key, value)


env = Env()

# Configuration settings
FETCH_VALIDATORS = "http://127.0.0.1:3006/get_validators_info?inode=DhWyMUj2pna2UYbvrqULyLf6dEo2MNzPHA7Uh4kBrJGFY"
CORE_URL = "http://127.0.0.1:3006"
INODE_IP = "127.0.0.1"
INODE_PORT = 65432
INODE_BUFFER = 1024

# Other configurations
INODE_WALLET_ADDRESS = "DhWyMUj2pna2UYbvrqULyLf6dEo2MNzPHA7Uh4kBrJGFY"
INODE_REWARD_WALLET_ADDRESS = "Djxhpx8ogGwpfe1tHxuBLVuxXZEhrS7spstDuXUugJ32i"
PRIVATEKEY = env.PRIVATEKEY
API_URL = "http://127.0.0.1:3006"
FAST_API_URL = "0.0.0.0"
FAST_API_PORT = 8000
TRACK = 500
