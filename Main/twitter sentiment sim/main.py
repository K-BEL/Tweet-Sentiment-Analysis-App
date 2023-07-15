from tweepy import OAuthHandler
from tweepy import Stream
import json
import snscrape.modules.twitter as sntwitter
import pandas as pd
import sys
import pytz
from datetime import datetime
from config import *
#from tweepy.streaming import StreamListener
from textblob import TextBlob
from elasticsearch import Elasticsearch
#from google_api_handler import GoogleAPIHandler
import requests

class GoogleAPIHandler:
    def __init__(self, key):
        """Google map API Handler
        Args:
            key(str): google developer key for the API
        """
        self.key = key
    
    def get_geo_info(self, latitude, longitude):
        """Get country name based on the coordinates of the tweets uisng Google Map API
        See https://developers.google.com/maps/documentation/geocoding/start#reverse
        Args:
            latitude(str)
            longitude(str)
        """

        country = None
        resp = None

        # Get latitude/longitude
        latlng = latitude + ',' + longitude
        
        # Request Google API
        link = ("https://maps.googleapis.com/maps/api/geocode/json?latlng=" +
                latlng + "&key=" + self.key)
        resp = requests.get(link)

        if resp:
            for result in resp.json()['results']:
                for item in result["address_components"]:
                    if 'country' in item['types']:
                        country = item["long_name"]
                        break
                    if country is not None:
                        break
        
        return country

# Import twitter keys and tokens
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
    

# Import listener
#from tools.tweet_listener import TweetStreamListener

def main():
    """Pipelines"""

    # Obtain the input topics of your interests
    topics = []
    if len(sys.argv) == 1:
        # Default topics
        topics = ['SpiderManNoWayHome']
    else:
        for topic in sys.argv[1:]:
            topics.append(topic)
    
    # Change this if you're not happy with the index and type names
    index = "spidey-sentiment"
    doc_type = "new-tweet"

    print("==> Topics", topics)
    print("==> Index: {}, doc type: {}".format(index, doc_type))
    print("==> Start retrieving tweets...")

    # Create instance of the tweepy tweet stream listener
    listener = TweetStreamListener(
                        index,
                        doc_type
                        )
    # Creating list to append tweet data to
    tweets_list1 = []

    for t in topics:
        # Using TwitterSearchScraper to scrape data and append tweets to list
        for i,tweet in enumerate(sntwitter.TwitterSearchScraper(t).get_items()):
            if i>100:
                break
            listener.on_data(tweet.content)



if __name__ == '__main__':
    main()
