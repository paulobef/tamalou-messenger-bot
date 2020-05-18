import random
from flask import Flask, request, session
from flask_redis import FlaskRedis
from pymessenger.bot import Bot
from os import environ
import json

app = Flask(__name__)
app.config.from_object('config.Config')     # Initializing our Flask application
redis_client = FlaskRedis(app, decode_responses=True)
# Messenger tokens
ACCESS_TOKEN = environ.get('ACCESS_TOKEN')
VERIFY_TOKEN = environ.get('VERIFY_TOKEN')
bot = Bot(ACCESS_TOKEN)

# Importing standard route and two requst types: GET and POST.
# We will receive messages that Facebook sends our bot at this endpoint
@app.route('/', methods=['GET', 'POST'])
def receive_message():
    if request.method == 'GET':
        # Before allowing people to message your bot Facebook has implemented a verify token
        # that confirms all requests that your bot receives came from Facebook.
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)
    # If the request was not GET, it  must be POSTand we can just proceed with sending a message
    # back to user
    else:
        # get whatever message a user sent the bot
        output = request.get_json()
        for event in output['entry']:
            messaging = event['messaging']
            message = messaging[0]
            # handle postbacks
            if 'postback' in message: 
                recipient_id = message['sender']['id']
                postback = message['postback']
                payload = postback['payload']
                if postback.get('referral') and payload == "Démarrer":
                    response_text = "Salut, comment ça va ?"
                    button_list = create_json_button_list(['😁', '😊', '😕'])
                    try:
                        bot.send_button_message(recipient_id, response_text, button_list)
                        print('send button should be working')
                    except:
                        print("send_button_message didn't work")
                    return "ok", 200
                if payload in ['😁', '😊', '😕', '🙁']:
                    try:
                        set_in_session(recipient_id, 'smiley', payload)
                    except:
                        raise Exception
                    response_text = "Dis-m'en plus !"
                    bot.send_text_message(recipient_id, response_text)
                    return "ok", 200
            # handle messages
            if message.get('message'):
                # Facebook Messenger ID for user so we know where to send response back to
                recipient_id = message['sender']['id']
                if message['message'].get('text'):
                    text = message['message']['text']
                    #send_message(recipient_id, text)
                    if (text == "Salut Tamalou"):
                        empty_session(recipient_id)
                        response_text = "Salut, comment ça va ?"
                        button_list = create_json_button_list(['😁', '😊', '😕'])
                        bot.send_button_message(recipient_id, response_text, button_list)
                        return "ok", 200
                    else:
                        add_to_session_messages(recipient_id, text)
                        smiley = get_in_session(recipient_id, 'smiley')
                        if smiley in ['😁', '😊']:
                            bot.send_text_message(recipient_id, 'Super ! Voici des contenus en lien avec ta situation')
                            bot.send_text_message(recipient_id, get_recommended_content_url()) # use ML service
                            return "ok", 200
                        else:
                            if all_topics_treated(recipient_id):
                                bot.send_text_message(recipient_id, 'Merci ! Voici des contenus en lien avec ta situation')
                                bot.send_text_message(recipient_id, get_recommended_content_url()) # use ML service
                                print(empty_session(recipient_id))
                                print(redis_client.hgetall(recipient_id))
                                return "ok", 200
                            else:
                                treated_topics = get_treated_topic()
                                print(treated_topics) # use ML service
                                for topic_name in treated_topics:
                                    set_treated_topic(recipient_id, topic_name)
                                reopening_text = get_highest_priority_reopening(treated_topics)
                                bot.send_text_message(recipient_id, reopening_text)
                                return "ok", 200


    return "ok", 200


def verify_fb_token(token_sent):
    # take token sent by Facebook and verify it matches the verify token you sent
    # if they match, allow the request, else return an error
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'


def get_message():
    sample_responses = ["You are stunning!", "We're proud of you",
                        "Keep on being you!", "We're greatful to know you :)"]
    # return selected item to the user
    return random.choice(sample_responses)

# Add description here about this if statement.
if __name__ == "__main__":
    app.run()


# Tamalou topic map
topic_map = [
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

  

# Tamalou services
def add_to_session_messages(session_id, text):
    previous_content = get_in_session(session_id, 'message')
    if (previous_content):
        set_in_session(session_id, 'message', f'{previous_content} {text}')
    else:
        set_in_session(session_id, 'message', text)

def is_topic_treated(session_id, key_name):
    return redis_client.hexists(session_id, key_name)

def all_topics_treated(session_id):
    session_key_list = redis_client.hkeys(session_id)
    print(session_key_list)
    for topic in topic_map:
        if topic['name'] not in session_key_list:
            return False
        return True

def set_treated_topic(session_id, key_name):
    set_in_session(session_id, key_name, 'True')

def empty_treated_topics(session_id):
    topic_names = []
    for topic in topic_map:
        topic_names.append(topic['name'])
    redis_client.hdel(session_id, *topic_names)

def empty_message(session_id):
    redis_client.hdel(session_id, 'message')

def empty_session(session_id):
    session_content_list = redis_client.hgetall(session_id)
    if (len(session_content_list) > 0):
        list = []
        for key,value in session_content_list.items():
            list.append(key)    
        redis_client.hdel(session_id, *list)
        return "session emptied"
    return "session already emptied"

def get_highest_priority_reopening(treated_topics):
    reopening = ""
    priority = 0
    for topic in topic_map:
        if (topic['priority_level'] >= priority and (topic['name'] not in treated_topics)):
            reopening = topic['reopening']
            priority = topic['priority_level']
    return reopening

def create_json_button_list(title_list):
    button_list = []
    for title in title_list:
        button_list.append({
            "type": "postback",
            "title": title,
            "payload": title
        })
    return json.dumps(button_list)

# redis utils
def set_in_session(session_id, key, value):
    redis_client.hmset(session_id, {
        key: value
    })
    return 'done'


def get_in_session(session_id, key):
    if redis_client.hexists(session_id, key):
        return redis_client.hget(session_id, key)
    else:
        return False


# ML simulators
def get_treated_topic():
    # TODO: integrate machine learning model
    return random.sample(["humeur", "intensite", "evolution", "contexte", "inquietude", "temporalite"], 2)

def get_recommended_content_url():
    # TODO: integrate machine learning model
    return 'https://www.doctissimo.fr/'

