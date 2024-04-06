from database.database import r, test_redis_connection


def get_pool_list_from_redis(key):
    try:

        if not test_redis_connection():
            print("Redis connection is not established.")
            return None

        pool_list = r.hgetall(key)

        if pool_list:
            print(f"PoolList retrieved successfully: {pool_list}")
            return pool_list
        else:
            print("PoolList does not exist or is empty.")
            return None
    except Exception as e:

        print(f"An error occurred while retrieving the PoolList: {e}")
        return None


if __name__ == "__main__":
    key = "PoolList"
    pool_list = get_pool_list_from_redis(key)
