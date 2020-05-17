import random
from flask import Flask, request, session
from flask_session import Session
from pymessenger.bot import Bot
from os import environ

app = Flask(__name__)       # Initializing our Flask application
Session(app)
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
            for message in messaging:
                if 'postback' in message:
                    recipient_id = message['sender']['id']
                    response_text = "Salut, comment ça va ?"
                    bot.send_button_message(recipient_id, response_text, ['😁', '😊', '😕', '🙁'])
                if message.get('message'):
                    # Facebook Messenger ID for user so we know where to send response back to
                    recipient_id = message['sender']['id']
                    if message['message'].get('text'):
                        text = message['message']['text']
                        recipient_id = message['sender']['id']
                        if (text == 'Salut Tamalou'):
                            response_sent_text = get_message() 
                            send_message(recipient_id, response_sent_text)
                            response_text = "Salut, comment ça va ?"
                            bot.send_button_message(recipient_id, response_text, ['😁', '😊', '😕', '🙁'])
                        if (text == '😁' | text == '😊'| text == '😕' | text == '🙁'):
                            session['smiley'] = text
                            bot.send_message(recipient_id, "Dis-m'en plus !")
                        else:
                            add_to_session_messages(text)
                            smiley = session.get('smiley')
                            if (smiley == '😁' | smiley == '😊'):
                                send_message(recipient_id, get_message())
                                send_message(recipient_id, get_recommended_content_url())
                            else:
                                if all_topics_treated():
                                    send_message(recipient_id, get_recommended_content_url())
                                    empty_message()
                                    empty_treated_topics()
                                else:
                                    treated_topics = get_treated_topic() # send message to ML service
                                    for topic_name in treated_topics:
                                        set_treated_topic(topic_name)
                                    send_reopening = get_highest_priority_reopening()
                                    send_message(recipient_id, send_reopening)

            







                    

                        #################### 
                        # TODO:
                        # on receive_message check if all topics are treated,               
                        # if all topics are not treated yet  
                        # session['key'] = 'value'                               
                        # - send message['message']['text'] to ML *relance* service.
                        # then receive boolean response from ML service, 
                        # - send *relance* to user based on (hard coded) *relance* in the app,
                        # - mark topic as "treated" in topic list (in session).
                        # elif all topics are treated, 
                        # - send message['message']['text'] to ML *recommendation* service
                        # then receive url/text from ML service
                        # - send url/text to user
                        # empty all session data
                        #####################


                        

                        response_sent_text = get_message() 
                        send_message(recipient_id, response_sent_text)
                    # if user send us a GIF, photo, video or any other non-text item
                    if message['message'].get('attachments'):
                        response_sent_text = get_message()
                        send_message(recipient_id, response_sent_text)
    return "Message Processed"


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

# Uses PyMessenger to send response to the user
def send_message(recipient_id, response):
    # sends user the text message provided via input response parameter
    bot.send_text_message(recipient_id, response)
    return "success"


# Add description here about this if statement.
if __name__ == "__main__":
    app.run()


# Tamalou topic map
topic_map = [
    {
        "name": "Humeur",
        "reopening": "humeur reopening",
        "priority_level": 1
    },
    {
        "name": "Inquiétude",
        "reopening": "inquiétude reopening",
        "priority_level": 2
    },
    {
        "name": "Temporalité",
        "reopening": "temporalité reopening",
        "priority_level": 3
    },
    {
        "name": "Contexte",
        "reopening": "contexte reopening",
        "priority_level": 4
    },
    {
        "name": "Intensité",
        "reopening": "intensité reopening",
        "priority_level": 5
    },
    {
        "name": "Evolution",
        "reopening": "intensité reopening",
        "priority_level": 6
    },
  ]

  

# Tamalou services
def add_to_session_messages(text):
    previous_content = session.get('message')
    if (previous_content):
        session['message'] = previous_content + ' ' + text
    else:
        session['message'] = text

def is_topic_treated(key_name):
    topic = session.get(key_name)
    if (topic):
        return True
    else:
        return False

def all_topics_treated():
    treated_topics = []
    for topic in topic_map:
        if (is_topic_treated(topic.name)):
            treated_topics.append(topic.name)
    return (len(topic_map) == len(treated_topics))

def set_treated_topic(key_name):
    session[key_name] = True

def empty_treated_topics():
    for topic in topic_map:
        session.pop(topic.name)

def empty_message():
    session.pop('message')

def get_highest_priority_reopening(treated_topics):
    reopening = ""
    priority = 0
    for topic in topic_map:
        if (topic['priority_level'] > priority & topic['name'] not in treated_topics):
            reopening = topic['reopening']
            priority = topic['priority_level']
    return reopening

# ML simulators
def get_treated_topic():
    # TODO: integrate machine learning model
    return ["Humeur", "Inquiétude"]

def get_recommended_content_url(message):
    # TODO: integrate machine learning model
    return 'https://dcap-research.fr/'
