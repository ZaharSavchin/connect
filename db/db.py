import json
from redis import Redis

user_dict: dict[int, dict[str, str | int | bool]] = {}

r = Redis(host='127.0.0.1', port=6379, db=7)


user_dict_json = r.get('users_db_connect')
if user_dict_json is not None:
    user_dict = json.loads(user_dict_json)
    user_dict = {int(k): v for k, v in user_dict.items()}
else:
    user_dict = {}


async def save_user_dict():
    r.set('users_db_connect', json.dumps(user_dict))
