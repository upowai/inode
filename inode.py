import socket
import threading
import redis
import json
from datetime import datetime
import signal
import sys
import logging
from api.api_client import fetch_block, test_api_connection
import utils.config as config
from utils.validator_utils import get_percentage
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidSignature
import os
import base64
from database.mongodb import test_db_connection, jobs_collection
from database.database import r, test_redis_connection
from dotenv import load_dotenv

# API
from fastapi import FastAPI, HTTPException, Request
import uvicorn
from api.api import router as validators_router
from fastapi.middleware.cors import CORSMiddleware
from utils.validator_utils import start_periodic_update, get_transactions_for_wallet


dotenv_path = ".env"
load_dotenv(dotenv_path)

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


class MessageType:
    VALIDATEMODEL = "validateModel"
    REQUESTJOB = "requestJob"
    SETCONFIG = "setConfig"


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(validators_router)


def run_fastapi():
    uvicorn.run(app, host=config.FAST_API_URL, port=config.FAST_API_PORT)


IP = config.INODE_IP
PORT = config.INODE_PORT
BUFFER_SIZE = config.INODE_BUFFER


logging.basicConfig(
    level=logging.INFO, format=" %(asctime)s %(levelname)s:%(message)s "
)


try:
    pem_private_key = base64.b64decode(b64_private_key)
    private_key = serialization.load_pem_private_key(
        pem_private_key,
        password=None,
    )
except Exception as e:
    logging.error(f"Error loading private key: {e}")
    raise


def decrypt_message(private_key, encrypted_message):
    try:
        return private_key.decrypt(
            encrypted_message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
    except InvalidSignature:
        raise ValueError("Invalid signature")
    except Exception as e:
        logging.error(f"Error in decryption: {e}")
        raise ValueError("Decryption failed")


@app.post("/modify-pool-list/")
async def modify_pool_list(request: Request):
    try:
        body = await request.body()
        decrypted_message = decrypt_message(private_key, body)
        action, publickey_value = decrypted_message.decode().split(":")

        value_to_store = json.dumps({"wallet_address": publickey_value})

        if action == "add":
            r.hset("PoolList", publickey_value, value_to_store)
            return {"status": "added", "publickey": publickey_value}
        elif action == "remove":
            r.hdel("PoolList", publickey_value)
            return {"status": "removed", "publickey": publickey_value}
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
    except ValueError as e:
        logging.error(f"Value error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"modify_pool_list Unexpected error: {e}")
        # Handle unexpected errors gracefully
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/transaction-history/{wallet_address}/{page}/{limit}")
async def transaction_history(wallet_address: str, page: int, limit: int):
    if page < 1 or limit < 1:
        raise HTTPException(
            status_code=400, detail="Page and limit must be greater than 0"
        )
    try:
        transactions = get_transactions_for_wallet(wallet_address, page, limit)
        if transactions:
            return {
                "wallet_address": wallet_address,
                "page": page,
                "limit": limit,
                "transactions": transactions,
            }
        else:
            raise HTTPException(
                status_code=404, detail="No transactions found for this wallet address"
            )
    except Exception as e:
        logging.error(f"transaction_history An error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred")


def job_processed(data):
    content = data.get("content", {})
    wallet_address = content.get("wallet_id")
    job_inode_list = r.lrange("jobInode", 0, -1)
    job_inode_list = [json.loads(job.decode("utf-8")) for job in job_inode_list]
    index = 0
    while index < len(job_inode_list):
        job = job_inode_list[index]

        if job["status"] == "complete":
            r.lrem("jobInode", 0, json.dumps(job))
            logging.info(f"Deleted completed job: {job['jobname']}")
            job_inode_list.pop(index)

            continue

        elif job["wallet_address"] is None:
            job["wallet_address"] = wallet_address
            r.lset("jobInode", index, json.dumps(job))
            logging.info(
                f"Updated job: {job['jobname']} with wallet address: {wallet_address}"
            )
            return job

        index += 1
    else:
        logging.error("No job with null wallet address found.")
        return None


def update_validator_data(data):
    try:
        content = data.get("content", {})
        ip = content.get("ip")
        port = content.get("port")
        wallet_address = content.get("wallet_address")
        ping = content.get("ping")

        if r.hexists("validators_list", wallet_address):
            current_data = r.hget("validators_list", wallet_address)
            current_data = json.loads(current_data)

            current_data["ip"] = ip
            current_data["port"] = port
            current_data["ping"] = ping

            r.hset("validators_list", wallet_address, json.dumps(current_data))
            return f"Validator data updated for wallet {wallet_address}"
        else:
            logging.error(f"No validator found with wallet address {wallet_address}")

    except redis.ConnectionError:
        logging.error(
            "Failed to connect to Redis. Please check your Redis server and connection details."
        )
    except json.JSONDecodeError:
        logging.error(
            "Failed to decode JSON data. Please check the data format in Redis."
        )
    except Exception as e:
        logging.error(f"update_validator_data An unexpected error occurred: {e}")


def handle_client(client_socket, client_address):
    try:
        BUFFER_SIZE = 1024

        data = client_socket.recv(BUFFER_SIZE).decode("utf-8")
        data = json.loads(data)

        response_message = "Default response or error message"

        if data.get("type") == MessageType.VALIDATEMODEL:
            validator_(client_socket, data)
        elif data.get("type") == MessageType.REQUESTJOB:
            job_name = job_processed(data)
            if job_name:
                response_message = json.dumps(job_name)
                # print("response message:", response_message)
            else:
                response_message = "No job updated"
        elif data.get("type") == MessageType.SETCONFIG:
            update_validator_data(data)
        else:
            raise ValueError("Unknown message type")

        # response_messageX = "Data processed successfullyX"

        client_socket.send(response_message.encode("utf-8"))

    except Exception as e:
        logging.error(f"Error handling client: {e}")
        client_socket.send(f"Error: {str(e)}".encode("utf-8"))
    finally:
        client_socket.close()


def validator_(client_socket, data):
    content = data.get("content", {})

    job_id = content.get("job_id")
    miner_pool_wallet = content.get("miner_pool_wallet")
    validator_wallet = content.get("validator_wallet")
    job_details = content.get("job_details")

    validator_percentage = get_percentage(validator_wallet)
    if validator_percentage is None:
        # print("Invalid validator wallet")
        client_socket.send("Invalid validator wallet".encode("utf-8"))
        return

    validator_details = r.hget("validators_list", validator_wallet)
    if validator_details:

        details = json.loads(validator_details)
    else:
        client_socket.send("Validator wallet not found".encode("utf-8"))
        return

    minerpool_details = r.hget("miners_list", miner_pool_wallet)

    if minerpool_details:
        pooldetails = json.loads(minerpool_details)

    else:
        client_socket.send("Miner pool wallet not found".encode("utf-8"))
        return

    job = jobs_collection.find_one({"_id": job_id})

    if not job:
        job = {
            "_id": job_id,
            "miner_pool_wallet": miner_pool_wallet,
            "job_details": job_details,
            "status": "processing",
            "percentage": 0,
            "validators": [],
            "created_at": datetime.utcnow(),
        }
        jobs_collection.insert_one(job)

    current_percentage = job.get("percentage", 0)
    existing_validators = job.get("validators", [])

    if current_percentage < 100:
        if validator_wallet not in existing_validators:
            existing_validators.append(validator_wallet)
            new_percentage = min(current_percentage + validator_percentage, 100)

            # Update validator details
            details["score"] = 1
            details["last_active_time"] = datetime.utcnow().isoformat()
            r.hset("validators_list", validator_wallet, json.dumps(details))

            # Update miner pool details
            pooldetails["score"] = 1
            pooldetails["last_active_time"] = datetime.utcnow().isoformat()
            r.hset("miners_list", miner_pool_wallet, json.dumps(pooldetails))

            update_fields = {
                "validators": existing_validators,
                "percentage": new_percentage,
            }
            if new_percentage == 100:
                update_fields["status"] = "completed"

            jobs_collection.update_one({"_id": job_id}, {"$set": update_fields})

            client_socket.send(
                f"Validator Successfully validated the job {job_id}".encode("utf-8")
            )
            return
        else:
            client_socket.send(
                "Validator has already validated this job".encode("utf-8")
            )
            return
    else:
        client_socket.send("Job has reached maximum percentage".encode("utf-8"))
        return


def signal_handler(sig, frame):
    logging.info(" Shutting down the server...")
    sys.exit(0)


def start_server(IP, PORT):
    fastapi_thread = threading.Thread(daemon=True, target=run_fastapi)
    fastapi_thread.start()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((IP, PORT))
        server.listen(5)
        logging.info(f" Server started on {IP}:{PORT}")

        start_periodic_update()

        while True:
            client_socket, client_address = server.accept()
            logging.info(f" Accepted connection from {client_address}")
            client_handler = threading.Thread(
                daemon=True, target=handle_client, args=(client_socket, client_address)
            )
            client_handler.start()

    except Exception as e:
        logging.error(f" An error occurred at start_server: {e}")
    finally:
        server.close()
        logging.info(" Server closed.")


if __name__ == "__main__":
    if not test_db_connection():
        logging.error("Failed to establish MongoDB connection. Exiting...")
        sys.exit(1)
    if not test_redis_connection():
        logging.error("Failed to establish Redis connection. Exiting...")
        sys.exit(2)
    if not test_api_connection(config.API_URL):
        logging.error("Failed to establish API connection. Exiting...")
        sys.exit(3)
    start_server(IP, PORT)
