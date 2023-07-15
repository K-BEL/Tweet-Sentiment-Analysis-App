import json
import pytz
from datetime import datetime
from tweepy import Stream

from config import *


#from tweepy.streaming import StreamListener
from textblob import TextBlob
from elasticsearch import Elasticsearch

from google_api_handler import GoogleAPIHandler

class TweetStreamListener():
    def __init__(self, index, doc_type):
        #super(TweetStreamListener, self).__init__(consumer_key,consumer_secret,access_token,access_token_secret)

        self.index = index
        self.doc_type = doc_type
        self.google_api_key = None

    def on_data(self, data):
        """"On success.
        To retrieve, process and organize tweets to get structured data
        and inject data into Elasticsearch
        """

        print("=> Retrievd a tweet")

        # Decode json
        #dict_data = json.loads(data)
        dict_data = (data)


        # Process data
        polarity, subjectivity, sentiment = self._get_sentiment(dict_data)
        print("[sentiment]", sentiment)
        print("[polarity]", polarity)



        # Inject data into Elasticsearch
        doc = {
               "polarity": polarity,
               "subjectivity": subjectivity,
               "sentiment": sentiment,
             }
        
        es = Elasticsearch("http://elastic:changeme@localhost:9200")
        es.index(index=self.index,
                 doc_type=self.doc_type,
                 body=doc)

        return True

    def on_error(self, status):
        """On failure"""
        print(status)
    
    def _get_sentiment(self, decoded):
        # Pass textual data to TextBlob to process
        tweet = TextBlob(decoded)

        # [0, 1] where 1 means very subjective
        subjectivity = tweet.sentiment.subjectivity
        # [-1, 1]
        polarity = tweet.sentiment.polarity
        
        # Determine if sentiment is positive, negative, or neutral
        if polarity < 0:
            sentiment = "negative"
        elif polarity == 0:
            sentiment = "neutral"
        else:
            sentiment = "positive"

        return polarity, subjectivity, sentiment
    
