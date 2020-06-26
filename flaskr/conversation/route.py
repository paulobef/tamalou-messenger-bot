from flaskr.conversation.services.content_suggestion import ContentSuggestionService
from flaskr.conversation.services.topics import TopicsService
from flask import Blueprint, request, current_app
from pymessenger.bot import Bot
from flaskr.utils.download_models import download_models
from flaskr.utils.redis_session import RedisSession
from flaskr import redis_client, DropboxConnector
import json
from typing import List
import dropbox

config = current_app.config

# Bot SDK (pymessenger)
bot = Bot(config['ACCESS_TOKEN'])

# initiate content suggester
suggester = ContentSuggestionService()

# register the route in the overall app
conversation = Blueprint('conversation', __name__, url_prefix='/conversation')


# Importing standard route and two request types: GET and POST.
# We will receive messages that Facebook sends our bot at this endpoint
@conversation.route('/webhook', methods=['GET', 'POST'])
def receive_message():
    if request.method == 'GET':
        # Before allowing people to message your bot Facebook has implemented a verify token
        # that confirms all requests that your bot receives came from Facebook.
        token_sent = request.args.get("hub.verify_token")
        if token_sent:
            return verify_fb_token(token_sent)
        else:
            return 'invalid token'
    # If the request was not GET, it  must be POST and we can just proceed with sending a message
    # back to user
    else:
        # get whatever message a user sent the bot
        output = request.get_json()
        for event in output['entry']:
            messaging = event['messaging']
            message = messaging[0]
            recipient_id = message['sender']['id']
            # we instantiate the custom server-side "session"
            # we use this instead of Flask-Session because there is no session attached to the web hook
            session = RedisSession(recipient_id, redis_client)
            reopener = TopicsService(session)
            # handle postbacks
            if 'postback' in message:
                recipient_id = message['sender']['id']
                postback = message['postback']
                payload = postback['payload']
                if payload == "START":
                    session.delete()
                    intro_text = "Salut, bienvenue chez Tamalou !"
                    explication_text = "Je suis là pour prêter un oreille attentive à ton problème ou à tout ce que tu voudrais me dire. Parle-moi de ton mal de tête ou de ta chute à vélo, par exemple, et j'essaierai de te trouver du contenu qui pourrait t'aider. Et bien sûr je ne le répête à personne et je ne retiendrais pas ton nom ou d'autres infos personnelles."
                    question_text = "Comment te sens-tu aujourd'hui ?"
                    send_multiple_text_messages(recipient_id, intro_text, explication_text)
                    button_list = create_json_button_list(['Super 😁!', 'Pas terrible 😕'])
                    bot.send_button_message(recipient_id, question_text, button_list)
                    return "ok", 200
                if payload == "RESTART":
                    session.delete()
                    intro_text = "Salut, content de te revoir !"
                    question_text = "Comment te sens-tu aujourd'hui ?"
                    button_list = create_json_button_list(['Super 😁!', 'Pas terrible 😕'])
                    bot.send_text_message(recipient_id, intro_text)
                    bot.send_button_message(recipient_id, question_text, button_list)
                    return "ok", 200
                if payload == "EXPLAIN":
                    session.delete()
                    intro_text = "Salut ! Voici un peu plus d'explication sur comment m'utiliser et pourquoi l'équipe " \
                                 "qui m'a mis au monde fait ce qu'elle fait. "
                    manifesto_text = "Toutes les maladies et souffrances de la vie ne peuvent pas être diagnostiquée " \
                                     "et soignée dans un simple rendez-vous chez le médecin. C'est pourquoi nous " \
                                     "croyons en l'implication du patient, de son ressenti personnelle pour combattre " \
                                     "l'errance diagnostic et aider patients et médecins à communiquer. La première " \
                                     "étape est d'être capable de recueillir ce ressenti subjectif, de l'interpréter " \
                                     "et de l'utiliser pour aider le patient. C'est ce que fait le Tamalou : il " \
                                     "t'écoute, te relance sur les points qu'il veut clarifier puis va chercher du " \
                                     "contenu en fonction de ce qu'il a compris du problème. "
                    briefing_text = "Un peu plus d'explication sur mon fonctionnement : \n J'utilise une technique " \
                                    "d'intelligence artificelle appartenant à la caétégorie de la compréhension du " \
                                    "language. \n\n Pour que le Tamalou comprenne au mieux ce que tu souhaite lui " \
                                    "dire : \n 1. Dis-en le plus possible \n 2. ne te sens pas obligé d'utiliser du " \
                                    "jargon \n\nSur le sujet de la confidentialité de tes données: \n1. Actuellement, " \
                                    "le Tamalou ne sait pas qui tu es et prend chaque conversation individuellement " \
                                    "\n2. Il n'enregistre pas les conversations au delà de la conversation en cours " \
                                    "\n3. Les deux points précédent sont susceptible de changer à mesure que le " \
                                    "Tamalou évolue, mais tu seras prévenu et aucune donnée ne sera rétroactivement " \
                                    "enregistrée "
                    send_multiple_text_messages(recipient_id, intro_text, manifesto_text, briefing_text)
                    return "ok", 200
                if payload in ['Super 😁!', 'Pas terrible 😕']:
                    session.set_key('smiley', payload)
                    response_text = "Dis-m'en plus !"
                    bot.send_text_message(recipient_id, response_text)
                    return "ok", 200
            # handle messages
            if 'message' in message:
                print('message in')
                # Facebook Messenger ID for user so we know where to send response back to
                if message['message'].get('text'):
                    text: str = message['message']['text']
                    if text == "Salut Tamalou" or text == "Démarrer":
                        session.delete()
                        response_text = "Salut, comment ça va ?"
                        button_list = create_json_button_list(['Super 😁!', 'Pas terrible 😕'])
                        bot.send_button_message(recipient_id, response_text, button_list)
                        return "ok", 200
                    elif text not in ['', ' ', '/', False, None]:
                        reopener.add_to_message(text)  # insert last message in aggregate of all session messages
                        complete_message: str = reopener.get_complete_message()  # retrieve aggregate as a string
                        print('Complete Message Stored: ' + complete_message)
                        smiley = session.get_key('smiley')
                        if smiley in ['Super 😁!']:
                            intro_text = 'Super ! Voici ce que j\'ai retenu de ce que tu m\'as dit :'
                            keyword_list_as_text = list_to_text(
                                suggester.extract_keywords(complete_message))  # use ML service
                            send_multiple_text_messages(recipient_id, intro_text, keyword_list_as_text)
                            session.delete()  # end session
                            return "ok", 200
                        else:
                            all_topics_treated = reopener.all_topics_treated()
                            print(all_topics_treated)
                            if all_topics_treated:
                                intro_text = 'Merci ! Voici ce que j\'ai retenu de ce que tu m\'as dit :'
                                next_text = "Et voici du contenu trouvé sur le web en lien avec ce que tu m'as dit"
                                keyword_list_as_text = list_to_text(
                                    suggester.extract_keywords(complete_message))  # use ML service
                                suggestions: list = suggester.get_results(keyword_list_as_text, 3)
                                print(suggestions)  # use Bing web search
                                send_multiple_text_messages(recipient_id, intro_text, keyword_list_as_text)
                                if suggestions == 'no results':
                                    session.delete()
                                    return "ok", 200
                                bot.send_text_message(recipient_id, next_text)
                                for suggestion in suggestions:
                                    text = suggestion['name'] + ': ' + suggestion['url']
                                    bot.send_text_message(recipient_id, text)
                                session.delete()  # end session
                                return "ok", 200
                            else:
                                current_treated_topics: List[str] = reopener.extract_treated_topics(complete_message)
                                for topic_name in current_treated_topics:
                                    reopener.set_treated_topic(topic_name)
                                session_treated_topics = reopener.get_all_treated_topics()
                                topic = reopener.get_highest_priority_topic(session_treated_topics)
                                reopener.set_treated_topic(topic['name'])
                                bot.send_text_message(recipient_id, topic['reopening'])
                                return "ok", 200

    return "ok", 200


def verify_fb_token(token_sent):
    # take token sent by Facebook and verify it matches the verify token you sent
    # if they match, allow the request, else return an error
    if token_sent == config['VERIFY_TOKEN']:
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


def send_multiple_text_messages(recipient_id, *args):
    for arg in args:
        bot.send_text_message(recipient_id, arg)
    return "ok"
