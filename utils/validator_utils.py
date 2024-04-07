import requests
import json
import threading
import time
import redis
from datetime import datetime
import random
import utils.config as config
from api.fetchTransaction import process_all
from api.push import send_transaction
from database.database import r
import logging
import uuid
import shortuuid
import asyncio
from database.mongodb import transactionsCollection, transactions_collection
from decimal import Decimal, ROUND_DOWN


UPDATE_INTERVAL_VALIDATORS = 120
LAST_UPDATE = 120
SCORE_RESET_TIME = 10800

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s:%(levelname)s - %(message)s"
)


def get_percentage(wallet_address):
    try:
        details = r.hget("validators_list", wallet_address)

        if details is None:
            return "Wallet address not found in validators list."

        details = json.loads(details.decode("utf-8"))

        return details.get("percentage", "Percentage field not found.")

    except redis.RedisError as e:
        return f"Redis error: {e}"

    except Exception as e:
        return f"get_percentage Error: {e}"


def fetch_validators(validators):
    try:
        response = requests.get(validators)
        response.raise_for_status()

        return response.json()
    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("OOps: Something Else", err)
    return []


def update_validators_list():
    try:
        validator_data = fetch_validators(config.FETCH_VALIDATORS)
        total_stake_all_validators = sum(
            validator.get("totalStake", 0) for validator in validator_data[:60]
        )
        r.delete("validators_list")
        for validator in validator_data[:60]:
            wallet_address = validator.get("validator")
            votes = validator.get("vote", [])
            totalStake = validator.get("totalStake")

            # Summing up all vote counts for the validator
            vote_count_sum = sum(vote.get("vote_count", 0) for vote in votes)

            validator_details = r.hget("validators_list", wallet_address)
            if validator_details:
                details = json.loads(validator_details)
            else:
                details = {
                    "balance": 0,
                    "score": 0,
                    "ping": 0,
                    "ip": 0,
                    "port": 0,
                    "vote": vote_count_sum,
                    "totalStake": totalStake,
                }

            details["vote"] = vote_count_sum
            details["totalStake"] = totalStake
            if total_stake_all_validators > 0:
                percentage_stake = round(
                    (totalStake / total_stake_all_validators) * 100, 2
                )
                details["percentage"] = percentage_stake
            r.hset("validators_list", wallet_address, json.dumps(details))
    except Exception as e:
        print(f"update_validators_list An error occurred: {e}")


def update_miners_list():
    try:
        pool_list_miners = r.hgetall("PoolList")
        if not pool_list_miners:
            logging.info("PoolList is empty. No miners to update.")
            return

        for miner_key, miner_value in pool_list_miners.items():
            wallet_address = miner_key.decode("utf-8")

            if r.hexists("miners_list", wallet_address):
                # If the miner already exists, skip updating to preserve existing data
                continue

            details = {
                "balance": 0,
                "score": 0,
                "wallet_address": wallet_address,
                "last_active_time": 0,
            }
            details_json = json.dumps(details)
            try:
                r.hset("miners_list", wallet_address, details_json)
            except redis.RedisError as inner_e:
                logging.error(
                    f"Failed to update miner {wallet_address} in miners_list: {inner_e}"
                )
    except redis.RedisError as e:
        logging.error(f"Redis operation error: {e}")
    except Exception as e:
        logging.error(f"update_miners_list Unexpected error: {e}")


def last_update():
    try:
        lists_to_update = ("validators_list", "miners_list")
        current_time = datetime.utcnow()
        for list_key in lists_to_update:
            all_entries = r.hgetall(list_key)

            for entry_key, details in all_entries.items():
                details = json.loads(details.decode("utf-8"))

                last_active_time_str = details.get("last_active_time", None)
                if not last_active_time_str:
                    continue

                try:
                    last_active_time = datetime.fromisoformat(last_active_time_str)
                except ValueError:
                    logging.error(
                        f"Invalid date format for {list_key[:-5]} {entry_key.decode()}: {last_active_time_str}"
                    )
                    continue

                time_diff = current_time - last_active_time
                if time_diff.total_seconds() > SCORE_RESET_TIME:
                    details["score"] = 0
                    r.hset(list_key, entry_key, json.dumps(details))
                    logging.info(
                        f"Updated {list_key[:-5]} {entry_key.decode()}: score set to 0"
                    )

    except Exception as e:
        logging.error(f"last_update An error occurred: {e}")


async def sign_and_push_transactions(transactions):
    try:
        for transaction in transactions:
            private_key = config.PRIVATEKEY
            wallet_address = transaction.get("wallet_address")
            transaction_type = transaction.get("type")
            id = transaction.get("id")
            new_balance = transaction.get("new_balance")
            amounts = str(
                Decimal(new_balance).quantize(
                    Decimal("0.00000001"), rounding=ROUND_DOWN
                )
            )

            message = ""
            try:
                transaction_hash = await send_transaction(
                    private_key, wallet_address, amounts, message
                )
                if transaction_hash:
                    logging.info(
                        f"transaction_hash: {transaction_hash}, for: {wallet_address}, amt: {amounts}, type: {transaction_type}"
                    )
                    transactions_collection.update_one(
                        {"wallet_address": wallet_address},
                        {
                            "$push": {
                                "transactions": {
                                    "hash": transaction_hash,
                                    "amount": amounts,
                                }
                            }
                        },
                        upsert=True,
                    )
                else:
                    logging.error(
                        f"Transaction failed for wallet address {wallet_address}. No hash was returned."
                    )
            except Exception as e:
                error_message = str(e)
                if "You can spend max 255 inputs" in error_message:
                    num_inputs = int(error_message.split("not ")[-1])
                    max_inputs = 255
                    num_splits = -(-num_inputs // max_inputs)  # Ceiling division
                    split_amount = float(amounts) / num_splits
                    logging.info(
                        f"Splitting transaction for {wallet_address} into {num_splits} parts due to UTXO limit."
                    )
                    for _ in range(num_splits):
                        add_transaction_to_batch(
                            wallet_address, split_amount, f"split_{transaction_type}"
                        )

                    # Remove the original transaction that exceeded the input limit
                    transactionsCollection.delete_one({"id": id})
                else:
                    logging.error(
                        f"Error during transaction processing for {wallet_address}: {e}"
                    )

        # Remove successfully processed transactions from the MongoDB collection
        if transactions:
            transactions_ids = [t.get("id") for t in transactions]
            transactionsCollection.delete_many({"id": {"$in": transactions_ids}})
    except Exception as e:
        logging.error(f"Error during signing and pushing transactions: {e}")


def get_transactions_for_wallet(wallet_address, page, limit):
    offset = (page - 1) * limit
    wallet_transactions = transactions_collection.aggregate(
        [
            {"$match": {"wallet_address": wallet_address}},
            {
                "$project": {
                    "transactions": {"$slice": ["$transactions", offset, limit]},
                    "_id": 0,
                }
            },
        ]
    )

    transactions = list(wallet_transactions)
    if transactions:

        return transactions[0].get("transactions", [])
    else:
        return []


def process_all_transactions():
    try:
        # Fetch all transactions and sort them by timestamp
        all_transactions = list(transactionsCollection.find().sort("timestamp", 1))

        # Deduplicate transactions, keeping only the latest for each wallet address
        unique_transactions = {}
        for transaction in all_transactions:
            wallet_address = transaction["wallet_address"]
            unique_transactions[wallet_address] = transaction

        # Get the first 5 unique transactions based on the sorted order by timestamp
        pending_transactions = list(unique_transactions.values())[:5]

        if pending_transactions:
            # Since sign_and_push_transactions is an async function,
            # we need to run it inside an event loop
            asyncio.run(sign_and_push_transactions(pending_transactions))

        else:
            print("No pending transactions to process.")
    except Exception as e:
        print(f"Error during process_all_transactions_mongodb: {e}")


def add_transaction_to_batch(wallet_address, tokens_to_distribute, rewardType):
    try:

        # Create the transaction document
        transaction_document = {
            "id": str(uuid.uuid4()),
            "wallet_address": str(wallet_address),
            "new_balance": float(tokens_to_distribute),
            "timestamp": datetime.utcnow(),
            "type": rewardType,
        }

        # Insert the document into the collection
        transactionsCollection.insert_one(transaction_document)

    except Exception as e:
        print(f"Error add_transaction_to_batch: {e}")


def update_balance(tokens_for_validators, tokens_for_miners, tokens_for_inode):
    try:
        try:
            all_validators = r.hgetall("validators_list")
        except redis.RedisError as e:
            print(f"Redis error when fetching validators: {e}")
            all_validators = {}

        total_effective_stake = 0
        effective_stakes = {}
        for wallet_address, details in all_validators.items():
            try:
                details = json.loads(details.decode("utf-8"))
            except json.JSONDecodeError as e:
                print(f"JSON decode error for validator details: {e}")
                continue

            score = details.get("score", 0)
            vote = details.get("vote", 0)
            totalStake = details.get("totalStake", 0)

            if score == 1:
                try:
                    effective_stake = (totalStake * vote) / 10
                except Exception as e:
                    print(f"Error calculating effective stake: {e}")
                    continue

                effective_stakes[wallet_address] = effective_stake
                total_effective_stake += effective_stake

        print("total_effective_stake", total_effective_stake)

        for wallet_address, effective_stake in effective_stakes.items():
            try:
                details = json.loads(all_validators[wallet_address].decode("utf-8"))
                proportion = (
                    effective_stake / total_effective_stake
                    if total_effective_stake > 0
                    else 0
                )
                tokens_to_distribute = proportion * tokens_for_validators
                rewardType = "validator_reward"
                add_transaction_to_batch(
                    wallet_address, tokens_to_distribute, rewardType
                )
            except Exception as e:
                print(f"Error processing validator reward distribution: {e}")

        # Process miners
        try:
            all_miners = r.hgetall("miners_list")
        except redis.RedisError as e:
            print(f"Redis error when fetching miners: {e}")
            all_miners = {}

        eligible_miners = []
        for wallet, details in all_miners.items():
            try:
                if json.loads(details.decode("utf-8")).get("score", 0) == 1:
                    eligible_miners.append(wallet)
            except json.JSONDecodeError as e:
                print(f"JSON decode error for miner details: {e}")

        num_eligible_miners = len(eligible_miners)

        tokens_per_miner = (
            tokens_for_miners / num_eligible_miners if num_eligible_miners > 0 else 0
        )

        if tokens_per_miner > 0:
            for wallet_address in eligible_miners:
                try:
                    rewardType = "miner_reward"
                    add_transaction_to_batch(
                        wallet_address, tokens_per_miner, rewardType
                    )
                except Exception as e:
                    print(f"Error processing miner reward distribution: {e}")

        # Process inodes
        try:
            rewardType = "inode_reward"
            reward_address = config.INODE_REWARD_WALLET_ADDRESS
            add_transaction_to_batch(reward_address, tokens_for_inode, rewardType)
        except Exception as e:
            print(f"Error processing inode reward distribution: {e}")

    except Exception as e:
        print(f"Unexpected error during update_balance: {e}")


def create_job():
    try:
        random_id = shortuuid.ShortUUID().random(length=16)
        job_name = f"jobInode{random_id}"

        urls = [
            "https://raw.githubusercontent.com/upowai/DATASETS/main/0/hash/hashes.csv",
            "https://raw.githubusercontent.com/upowai/DATASETS/main/1/hash/hashes.csv",
            "https://raw.githubusercontent.com/upowai/DATASETS/main/2/hash/hashes.csv",
            "https://raw.githubusercontent.com/upowai/DATASETS/main/3/hash/hashes.csv",
        ]

        selected_url = random.choice(urls)

        wallet_address = None

        job_details = {
            "jobname": job_name,
            "wallet_address": wallet_address,
            "status": "pending",
            "hash": selected_url,
        }

        r.rpush("jobInode", json.dumps(job_details))

        # print("New Job Created", job_name)

        return job_name
    except redis.RedisError as e:
        print(f"Redis error occurred: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON serialization error: {e}")
    except requests.HTTPError as e:
        print(f"HTTP request error: {e}")
    except Exception as e:
        print(f"create_job An unexpected error occurred: {e}")


def update_validators_periodically():
    try:
        while True:
            update_validators_list()
            update_miners_list()
            info = process_all()
            if info is not None:
                update_balance(info["41%_1"], info["41%_2"], info["18%"])
            else:
                logging.info(
                    "Skipping update_balance due to processing error or no data."
                )
            time.sleep(UPDATE_INTERVAL_VALIDATORS)
    except Exception as e:
        print(f"Error in update_validators_periodically: {e}")


def push_tx_periodically():
    try:
        while True:
            process_all_transactions()
            time.sleep(60)
    except Exception as e:
        print(f"Error in push_tx_periodically: {e}")


def last_update_periodically():
    try:
        while True:
            last_update()
            create_job()
            time.sleep(LAST_UPDATE)
    except Exception as e:
        print(f"Error in last_update_periodically: {e}")


def start_periodic_update():
    validators_thread = threading.Thread(
        target=update_validators_periodically, daemon=True
    )
    balance_thread = threading.Thread(target=last_update_periodically, daemon=True)
    tx_push = threading.Thread(target=push_tx_periodically, daemon=True)
    validators_thread.start()
    balance_thread.start()
    tx_push.start()
