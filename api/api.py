from fastapi import APIRouter, HTTPException
import redis

router = APIRouter()

from database.database import r


@router.get("/validators")
def get_validators():
    try:
        validators = r.hgetall("validators_list")
        if not validators:
            raise HTTPException(status_code=404, detail="No validators found")
        return validators
    except redis.RedisError as e:
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred XYZ: {str(e)}")
