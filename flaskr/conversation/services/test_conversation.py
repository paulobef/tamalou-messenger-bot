from fakeredis import FakeStrictRedis
from flaskr.conversation.services.topics import TopicsService
from flaskr.utils.redis_session import RedisSession


def test_conversation_service():
    redis_client = FakeStrictRedis(decode_responses=True)
    session = RedisSession('TEST_SESSION_ID_34XCDFE6789', redis_client)  # TODO replace with random test id
    conv = TopicsService(session)

    conv.add_to_message('text part 1')
    conv.add_to_message('text part 2')

    assert conv.get_complete_message() == 'text part 1 text part 2'

    for topic in conv.TOPIC_MAP:
        conv.set_treated_topic(topic['name'])
    assert conv.all_topics_treated() is True

    session.delete()
    assert conv.get_complete_message() is False
