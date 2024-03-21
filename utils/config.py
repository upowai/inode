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
FETCH_VALIDATORS = (
    "get_validators_info?inode=DbHgJVR7gDdTaxx7v3kX3GsxfJnTXy9zouSuzXE1TUWmB"
)
CORE_URL = "https://api.upow.ai"
INODE_IP = "0.0.0.0"
INODE_PORT = 65432
INODE_BUFFER = 1024

# Other configurations
INODE_WALLET_ADDRESS = "DbHgJVR7gDdTaxx7v3kX3GsxfJnTXy9zouSuzXE1TUWmB"
INODE_REWARD_WALLET_ADDRESS = "Djxhpx8ogGwpfe1tHxuBLVuxXZEhrS7spstDuXUugJ32i"
PRIVATEKEY = env.PRIVATEKEY
API_URL = "https://api.upow.ai"
FAST_API_URL = "0.0.0.0"
FAST_API_PORT = 8000
TRACK = 15616
