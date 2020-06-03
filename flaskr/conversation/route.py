
from flaskr.conversation.services.conversation import ConversationService
from flask import current_app as app
from flask import Blueprint, request
from pymessenger.bot import Bot
from os import environ
from flaskr import redis_client

from flaskr.utils.redis_session import RedisSession
import json

# Messenger tokens
ACCESS_TOKEN = environ.get('ACCESS_TOKEN')
VERIFY_TOKEN = environ.get('VERIFY_TOKEN')

# Bot SDK (pymessenger)
bot = Bot(ACCESS_TOKEN)

# register the route in the overall app
conversation = Blueprint('conversation', __name__, url_prefix='/conversation')

# Importing standard route and two requst types: GET and POST.
# We will receive messages that Facebook sends our bot at this endpoint
@conversation.route('/webhook', methods=['GET', 'POST'])
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
            session = RedisSession(recipient_id, redis_client) # custom server-side "session" communicator
            conv = ConversationService(session)
            # handle postbacks
            if 'postback' in message: 
                recipient_id = message['sender']['id']
                postback = message['postback']
                payload = postback['payload']
                if payload == "Démarrer":
                    response_text = "Salut, comment ça va ?"
                    button_list = create_json_button_list(['Super 😁!', 'Pas terrible 😕'])
                    try:
                        bot.send_button_message(recipient_id, response_text, button_list)
                        print('send button should be working')
                    except:
                        print("send_button_message didn't work")
                    return "ok", 200
                if payload in ['Super 😁!', 'Pas terrible 😕']:
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
                        button_list = create_json_button_list(['Super 😁!', 'Pas terrible 😕'])
                        bot.send_button_message(recipient_id, response_text, button_list)
                        return "ok", 200
                    else:
                        conv.add_to_message(text)
                        smiley = session.get_key('smiley')
                        if smiley in ['Super 😁!', 'Pas terrible 😕']:
                            bot.send_text_message(recipient_id, 'Super ! Voici ce que j\'ai retenu de ce que tu m\'as dit :')
                            keyword_list_as_text = list_to_text(conv.extract_keywords(session.get_key('message'))) # use ML service
                            bot.send_text_message(recipient_id, keyword_list_as_text) 
                            return "ok", 200
                        else:
                            if conv.all_topics_treated():
                                bot.send_text_message(recipient_id, 'Merci ! Voici ce que j\'ai retenu de ce que tu m\'as dit :')
                                keyword_list_as_text = list_to_text(conv.extract_keywords(session.get_key('message'))) # use ML service
                                bot.send_text_message(recipient_id, keyword_list_as_text) 
                                session.empty()
                                return "ok", 200
                            else:
                                treated_topics = conv.extract_treated_topics(session.get_key('message'))
                                for topic_name in treated_topics:
                                    conv.set_treated_topic(topic_name)
                                reopening_text = conv.get_highest_priority_reopening(treated_topics)
                                bot.send_text_message(recipient_id, reopening_text)
                                return "ok", 200


    return "ok", 200


def verify_fb_token(token_sent):
    # take token sent by Facebook and verify it matches the verify token you sent
    # if they match, allow the request, else return an error
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'

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


def list_to_text(list):
    text = ''
    for word in list:
        text += word + ' '
    return text