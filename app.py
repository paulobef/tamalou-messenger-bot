import random
from flask import Flask, request
from flask_redis import FlaskRedis
from pymessenger.bot import Bot
from redis_session import RedisSessionManager
from os import environ
import json
from feature.sensation.topics import TOPIC_MAP
from feature.sensation.conversation import SensationConversationUtils


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
            recipient_id = message['sender']['id']
            session = RedisSessionManager(recipient_id, redis_client) # custom server-side "session" communicator
            utils = SensationConversationUtils(session, TOPIC_MAP)
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
                        session.set_key('smiley', payload)
                    except:
                        raise Exception
                    response_text = "Dis-m'en plus !"
                    bot.send_text_message(recipient_id, response_text)
                    return "ok", 200
            # handle messages
            if 'message' in message:
                # Facebook Messenger ID for user so we know where to send response back to
                if message['message'].get('text'):
                    text = message['message']['text']
                    if (text == "Salut Tamalou"):
                        session.empty()
                        response_text = "Salut, comment ça va ?"
                        button_list = create_json_button_list(['😁', '😊', '😕'])
                        bot.send_button_message(recipient_id, response_text, button_list)
                        return "ok", 200
                    else:
                        utils.add_to_message(text)
                        smiley = session.get_key('smiley')
                        if smiley in ['😁', '😊']:
                            bot.send_text_message(recipient_id, 'Super ! Voici des contenus en lien avec ta situation')
                            bot.send_text_message(recipient_id, get_recommended_content_url()) # use ML service
                            return "ok", 200
                        else:
                            if utils.all_topics_treated():
                                bot.send_text_message(recipient_id, 'Merci ! Voici des contenus en lien avec ta situation')
                                bot.send_text_message(recipient_id, get_recommended_content_url()) # use ML service
                                session.empty()
                                return "ok", 200
                            else:
                                treated_topics = get_treated_topic(session.get_key('message'))
                                for topic_name in treated_topics:
                                    utils.set_treated_topic(topic_name)
                                reopening_text = utils.get_highest_priority_reopening(treated_topics)
                                bot.send_text_message(recipient_id, reopening_text)
                                return "ok", 200


    return "ok", 200


def verify_fb_token(token_sent):
    # take token sent by Facebook and verify it matches the verify token you sent
    # if they match, allow the request, else return an error
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'

# Add description here about this if statement.
if __name__ == "__main__":
    app.run()

# utils
def create_json_button_list(title_list):
    button_list = []
    for title in title_list:
        button_list.append({
            "type": "postback",
            "title": title,
            "payload": title
        })
    return json.dumps(button_list)

# ML simulators
def get_treated_topic(message):
    # TODO: integrate machine learning model
    print(message)
    return random.sample(["humeur", "intensite", "evolution", "contexte", "inquietude", "temporalite"], 4)

def get_recommended_content_url():
    # TODO: integrate machine learning model
    return 'https://www.doctissimo.fr/'






    

