from flaskr.utils.redis_session import RedisSession
from flaskr.conversation.services.topic_scoring import topic_scoring
from flaskr.conversation.services.get_keywords_from_french import get_keywords_from_french

class ConversationService:
    
    def __init__(self, session: RedisSession):
        self.session = session # must be RedisSessionManager instance 
        self.TOPIC_MAP = [
            {
                "name": "humeur",
                "reopening": "Tu te sens en forme ?",
                "priority_level": 8
            },
            {
                "name": "inquietude",
                "reopening": "Est-ce que cela t'inquiète ?",
                "priority_level": 7
            },
            {
                "name": "temporalite",
                "reopening": "Est-ce que ça dure depuis longtemps ? ça t'arrive souvent ?",
                "priority_level": 6
            },
            {
                "name": "contexte",
                "reopening": "Est-ce que tu pense que c'est lié à quelque chose ?",
                "priority_level": 5
            },
            {
                "name": "intensite",
                "reopening": "C'est une sensation plutôt forte ou légère ?",
                "priority_level": 4
            },
            {
                "name": "evolution",
                "reopening": "Est-ce que tu as ressenti une évolution ces derniers temps ?",
                "priority_level": 3
            },
        ]
        self.TREATED_TOPIC_SCORE_LIMIT = 0.5
    
    # util
    def get_highest_priority_reopening(self, treated_topics):
        reopening = ""
        priority = 0
        for topic in self.TOPIC_MAP:
            if (topic['priority_level'] >= priority and (topic['name'] not in treated_topics)):
                reopening = topic['reopening']
                priority = topic['priority_level']
        return reopening

    # Session interface
    def add_to_message(self, text):
        previous_content = self.session.get_key('message')
        if (previous_content):
            self.session.set_key('message', f'{previous_content} {text}')
        else:
            self.session.set_key('message', text)

    def all_topics_treated(self):
        session_key_list = self.session.get_all_keys()
        print(session_key_list)
        for topic in self.TOPIC_MAP:
            if topic['name'] not in session_key_list:
                return False
            return True

    def set_treated_topic(self, key_name):
        self.session.set_key(key_name, 'True')

    # Machine Learning interface
    def extract_treated_topics(self, text_in):
        score_list = topic_scoring(text_in)
        treated_topics = []
        for key, value in score_list:
            if value > self.TREATED_TOPIC_SCORE_LIMIT:
                treated_topics.append(key)
        return treated_topics
    
    def extract_keywords(self, text_in):
        return get_keywords_from_french(text_in)
            
        
 