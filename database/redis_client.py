from database.database import r
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s:%(levelname)s - %(message)s"
)


def set_last_block_height(block_height):
    try:
        # Ensure block_height is an integer to prevent data type issues
        block_height = int(block_height)
        r.set("last_block_height", block_height)
        return True
    except ValueError:
        logging.error("Invalid block_height type. Expected an integer.")
    except Exception as e:
        logging.error(f"Unexpected error setting last block height: {e}")
    return False


def get_last_block_height():
    try:
        # Attempt to retrieve and convert the value to an integer
        block_height = r.get("last_block_height")
        if block_height is None:
            # If the key does not exist, return None
            return None
        return int(block_height)
    except ValueError:
        # Handle case where the value is not an integer
        logging.error("Stored 'last_block_height' is not an integer.")
    except Exception as e:
        logging.error(f"Unexpected error retrieving last block height: {e}")
    return None
