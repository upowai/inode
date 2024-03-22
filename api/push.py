import logging
import requests
from upow_transactions.helpers import sha256
from utils.utils import Utils
import logging


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s:%(levelname)s - %(message)s"
)

wallet_utils: Utils = Utils()


def string_to_bytes(string: str) -> bytes:
    if string is None:
        return None
    try:
        return bytes.fromhex(string)
    except ValueError:
        return string.encode("utf-8")


def remove_b_prefix(byte_string):
    if isinstance(byte_string, bytes):
        return byte_string.decode("utf-8")
    elif (
        isinstance(byte_string, str)
        and byte_string.startswith("b'")
        and byte_string.endswith("'")
    ):
        return byte_string[2:-1]
    return byte_string


async def push_tx(tx, wallet_utils: Utils):
    try:
        r = requests.get(
            f"{wallet_utils.NODE_URL}/push_tx", {"tx_hex": tx.hex()}, timeout=10
        )
        r.raise_for_status()
        res = r.json()
        if res["ok"]:
            transaction_hash = sha256(tx.hex())
            logging.info(f"Transaction pushed. Transaction hash: {transaction_hash}")
            return transaction_hash  # Return the hash here
        else:
            logging.error("\nTransaction has not been pushed")
            return None  # Or handle this case as needed
    except Exception as e:
        logging.error(f"Error during request to node: {e}")
        return None  # Or handle this case as needed


async def send_transaction(private_key_hex, recipients, amounts, message=None):
    try:
        recipients = remove_b_prefix(recipients)
        logging.info(f"Private Key Hex: {private_key_hex}")
        logging.info(f"Recipients: {recipients}")
        logging.info(f"Amounts: {amounts}")
        private_key = int(private_key_hex, 16)
        recipients_list = recipients.split(",")
        amounts_list = amounts.split(",")
        logging.info(
            f"Recipients List: {recipients_list}, Amounts List: {amounts_list}"
        )
        message_bytes = string_to_bytes(message) if message else None

        if (
            len(recipients_list) > 1
            and len(amounts_list) > 1
            and len(recipients_list) == len(amounts_list)
        ):
            tx = await wallet_utils.create_transaction_to_send_multiple_wallet(
                private_key, recipients_list, amounts_list, message_bytes
            )
        else:
            receiver = recipients_list[0]
            amount = amounts_list[0]
            tx = await wallet_utils.create_transaction(
                private_key, receiver, amount, message_bytes
            )
        return await push_tx(tx, wallet_utils)  # Ensure this returns the hash
    except Exception as e:
        logging.error(f"Error in send_transaction: {e}")
        raise
