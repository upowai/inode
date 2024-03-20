import logging
import requests
import json
import utils.config as config
from pymongo.errors import PyMongoError
from database.redis_client import set_last_block_height, get_last_block_height
from database.mongodb import processed_transactions
from api.api_client import fetch_block, test_api_connection

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s:%(levelname)s - %(message)s"
)


def calculate_percentages(total_amount):
    percentages = {"18%": 0, "41%_1": 0, "41%_2": 0}
    percentages["18%"] = round(total_amount * 0.18, 8)
    percentages["41%_1"] = round(total_amount * 0.41, 8)
    percentages["41%_2"] = round(total_amount * 0.41, 8)
    return percentages


def insert_unique_transaction(hash_value):
    try:
        result = processed_transactions.update_one(
            {"hash": hash_value},
            {"$setOnInsert": {"hash": hash_value}},
            upsert=True,
        )
        if result.upserted_id is not None:
            # logging.info(f"Inserted new transaction with hash: {hash_value}")
            return True
        else:
            logging.info(f"Transaction with hash: {hash_value} already exists.")
            return False
    except PyMongoError as e:
        logging.error(
            f"Failed to insert or check transaction with hash: {hash_value}. Error: {e}"
        )
        return None


def process_all():
    try:
        last_block_height = get_last_block_height()

        if last_block_height is None:
            logging.info("No last block height found in Redis, using hardcoded value.")
            last_block_height = config.TRACK
        else:
            last_block_height += 1

        logging.info(f"Starting processing from block height: {last_block_height}")

        data = fetch_block(
            f"{config.API_URL}/get_blocks_details?offset={last_block_height}&limit=10"
        )

        if data is None or not data["result"]:
            logging.error("No block data retrieved or no new blocks since last check.")
            return None

        total_amount = 0
        last_block_id = None

        for block in data["result"]:
            block_id = block["block"]["id"]
            last_block_id = block_id

            for transaction in block["transactions"]:
                hash_value = transaction["hash"]
                transaction_amount = 0  # Initialize transaction amount

                if transaction.get("transaction_type", "REGULAR") != "REGULAR":
                    continue

                # Collect all input addresses for the current transaction
                input_addresses = [
                    input["address"] for input in transaction.get("inputs", [])
                ]

                # Check if the transaction is relevant and calculate its amount
                for output in transaction["outputs"]:
                    # Check if the output is for the indoe wallet address, the type is REGULAR, and the output address is not in the transaction's input addresses (not a self-transaction)
                    if (
                        output["address"] == config.INODE_WALLET_ADDRESS
                        and output["type"] == "REGULAR"
                        and output["address"] not in input_addresses
                    ):
                        transaction_amount += output["amount"]

                # Only proceed if the transaction is relevant and not already processed
                if transaction_amount > 0:
                    if insert_unique_transaction(hash_value):
                        # Add the transaction amount only if it's a new transaction
                        total_amount += transaction_amount
                    else:
                        logging.info(
                            f"Skipping already processed transaction: {hash_value}"
                        )

        if last_block_id is not None:
            set_last_block_height(last_block_id)
        else:
            logging.info("No new blocks to process.")

        if total_amount <= 0:
            logging.info(
                f"No relevant transactions found for {config.INODE_WALLET_ADDRESS} in the latest blocks."
            )
            return None

        percentages = calculate_percentages(total_amount)

        print("percentages", percentages, "total_amount", total_amount)

        return percentages

    except Exception as e:
        logging.error(f"An error occurred during process_all: {e}")
        return None
