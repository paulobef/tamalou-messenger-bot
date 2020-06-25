from azure.cognitiveservices.search.websearch import WebSearchClient
from msrest.authentication import CognitiveServicesCredentials
from flask import current_app
from flaskr.conversation.services.get_keywords_from_french import get_keywords_from_french

config = current_app.config


# Instantiate the client and replace with your endpoint.
class ContentSuggestionService:

    def __init__(self):
        # config var for Bing Web Search (Azure cloud)
        self.subscription_key = config['SUBSCRIPTION_KEY']
        self.endpoint = config['ENDPOINT']

    @staticmethod
    def extract_keywords(text_in):
        return get_keywords_from_french(text_in)

    def get_results(self, search_text, quantity):
        client = WebSearchClient(self.endpoint, CognitiveServicesCredentials(self.subscription_key))
        # Make a request. Replace Yosemite if you'd like.
        web_data = client.web.search(query=search_text)
        '''
        Web pages
        If the search response contains web pages, the first result's name and url
        are printed.
        '''
        if hasattr(web_data.web_pages, 'value'):
            print(len(web_data.web_pages.value))
            i = 0
            results = []
            for web_page in web_data.web_pages.value:
                if i < quantity:
                    page = {
                        "name": web_page.name,
                        "url": web_page.url
                    }
                    results.append(page)
                    i += 1
            return results
        else:
            print("Didn't find any web pages...")
            return "no results"
