from typing import Dict, Any
from flaskr.utils.redis_session import RedisSession
from flaskr.conversation.services.topic_scoring import topic_scoring


class TopicsService:

    def __init__(self, session: RedisSession):
        self.session = session  # must be RedisSession instance
        self.TOPIC_MAP = [
            {
                "name": "Humeur",
                "reopening": "Tu te sens en forme ?",
                "priority_level": 8,
                "treated_limit": 0.2
            },
            {
                "name": "Inquiétude",
                "reopening": "Est-ce que cela t'inquiète ?",
                "priority_level": 7,
                "treated_limit": 0.5
            },
            {
                "name": "Temporalité",
                "reopening": "Est-ce que ça dure depuis longtemps ? ça t'arrive souvent ?",
                "priority_level": 6,
                "treated_limit": 0.9
            },
            {
                "name": "Contexte",
                "reopening": "Est-ce que tu pense que c'est lié à quelque chose ?",
                "priority_level": 5,
                "treated_limit": 0.9
            },
            {
                "name": "Intensité",
                "reopening": "C'est une sensation plutôt forte ou légère ?",
                "priority_level": 4,
                "treated_limit": 0.5
            },
            {
                "name": "Evolution",
                "reopening": "Est-ce que tu as ressenti une évolution ces derniers temps ?",
                "priority_level": 3,
                "treated_limit": 0.9
            },
        ]
        # dict & list comprehension for easy usage of TOPIC MAP
        self.treated_limit_map = {topic['name']: topic['treated_limit'] for topic in self.TOPIC_MAP}
        self.topic_names = [topic['name'] for topic in self.TOPIC_MAP]

    # util
    def get_highest_priority_topic(self, treated_topics):
        hp_topic: dict = {}
        priority = 0
        for topic in self.TOPIC_MAP:
            if topic['priority_level'] >= priority and (topic['name'] not in treated_topics):
                hp_topic = topic
                priority = topic['priority_level']
        return hp_topic

    # Session interface
    def add_to_message(self, text: str):
        previous_content: str = self.session.get_key('message')
        if previous_content and previous_content != text:
            self.session.set_key('message', previous_content + ' ' + text)
        else:
            self.session.set_key('message', text)

    def get_complete_message(self):
        return self.session.get_key('message')

    def get_all_treated_topics(self):
        session_key_list = self.session.get_all_keys()
        return [word for word in session_key_list if word in self.topic_names]

    def all_topics_treated(self):
        session_key_list = self.session.get_all_keys()
        print('Keys currently in session: ' + ' '.join(session_key_list))
        yes = False
        for topic in self.TOPIC_MAP:
            if topic['name'] not in session_key_list:
                return False
        return True

    def set_treated_topic(self, key_name):
        self.session.set_key(key_name, 'True')

    # Machine Learning interface
    def extract_treated_topics(self, text_in):
        scores: Dict[str, float] = topic_scoring(text_in, 1)
        nice_print_dict(scores)
        treated_topics = []
        for topic in scores.keys():
            if scores[topic] >= self.treated_limit_map[topic]:
                treated_topics.append(topic)
        return treated_topics


# util for printing dict nicely to the console (for debugging and demos)
def nice_print_dict(_dict: Dict[str, Any]):
    output = ''
    for key in _dict.keys():
        output += key + ': ' + str(_dict[key]) + '\n'
    print(output)
