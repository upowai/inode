from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


def test_db_connection():
    try:
        client = MongoClient(
            "mongodb://localhost:27017/", serverSelectionTimeoutMS=5000
        )

        client.admin.command("ping")
        print("MongoDB connection established successfully.")
        return True
    except ConnectionFailure:
        print("Failed to connect to MongoDB.")
        return False


def get_db_connection():
    client = MongoClient("mongodb://localhost:27017/")
    return client.inode


# Initialize the connection
db = get_db_connection()
jobs_collection = db.jobs
processed_transactions = db.processedTransactions
transactionsCollection = db.transactionsCollection
transactions_collection = db.transactions
