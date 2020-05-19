
class SensationConversationUtils:
    
    def __init__(self, session, topic_map):
        self.session = session # must be RedisSessionManager instance 
        self.topic_map = topic_map

    def add_to_message(self, text):
        previous_content = self.session.get_key('message')
        if (previous_content):
            self.session.set_key('message', f'{previous_content} {text}')
        else:
            self.session.set_key('message', text)

    def all_topics_treated(self):
        session_key_list = self.session.get_all_keys()
        print(session_key_list)
        for topic in self.topic_map:
            if topic['name'] not in session_key_list:
                return False
            return True

    def set_treated_topic(self, key_name):
        self.session.set_key(key_name, 'True')

    def get_highest_priority_reopening(self, treated_topics):
        reopening = ""
        priority = 0
        for topic in self.topic_map:
            if (topic['priority_level'] >= priority and (topic['name'] not in treated_topics)):
                reopening = topic['reopening']
                priority = topic['priority_level']
        return reopening