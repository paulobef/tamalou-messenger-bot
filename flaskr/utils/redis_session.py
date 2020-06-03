'''
Implements "custom sessions" using redis hash data structure.
for use in messenger bot, pass the sender id as the session id (which is simply the hash name)
'''

class RedisSession:

    def __init__(self, session_id: str, redis_client):
        self.session_id = session_id
        self.redis_client = redis_client

    # Session methods
    def set_key(self, key, value):
        self.redis_client.hmset(self.session_id, {
            key: value
        })
        return 'done'

    def get_key(self, key):
        if self.redis_client.hexists(self.session_id, key):
            return self.redis_client.hget(self.session_id, key)
        else:
            return False

    def del_key(self, *args):
        self.redis_client.hdel(self.session_id, *args)
    
    def get_all_keys(self):
        return self.redis_client.hkeys(self.session_id)

    def get_all_entries(self):
        return self.redis_client.hgetall(self.session_id)
    
    def empty(self):
        session_content_list = self.redis_client.hgetall(self.session_id)
        if (len(session_content_list) > 0):
            list = []
            for key, value in session_content_list.items():
                list.append(key)    
            self.redis_client.hdel(self.session_id, *list)
            return "session emptied"
        return "session was already emptied"