from tweepy import OAuthHandler
from tweepy import Stream
import json
import snscrape.modules.twitter as sntwitter
import pandas as pd
import sys
import pytz
from datetime import datetime
from config import *
from textblob import TextBlob
from elasticsearch import Elasticsearch
import requests

class GoogleAPIHandler:
    def __init__(self, key):
        self.key = key
    
    def get_geo_info(self, latitude, longitude):
        country = None
        resp = None

        latlng = latitude + ',' + longitude
        
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

class TweetStreamListener():
    def __init__(self, index, doc_type):
        self.index = index
        self.doc_type = doc_type
        self.google_api_key = None

    def on_data(self, data):

        print("=> Retrievd a tweet")

        dict_data = (data)

        polarity, subjectivity, sentiment = self._get_sentiment(dict_data)
        print("[sentiment]", sentiment)
        print("[polarity]", polarity)


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
        tweet = TextBlob(decoded)

        subjectivity = tweet.sentiment.subjectivity
        polarity = tweet.sentiment.polarity
        
        if polarity < 0:
            sentiment = "negative"
        elif polarity == 0:
            sentiment = "neutral"
        else:
            sentiment = "positive"

        return polarity, subjectivity, sentiment
    

def main():

    topics = []
    if len(sys.argv) == 1:
        topics = ['Congress']
    else:
        for topic in sys.argv[1:]:
            topics.append(topic)
    
    index = "tweet_sentiment_apple"
    doc_type = "new-tweet"

    print("==> Topics", topics)
    print("==> Index: {}, doc type: {}".format(index, doc_type))
    print("==> Start retrieving tweets...")

    listener = TweetStreamListener(
                        index,
                        doc_type
                        )
    tweets_list1 = []

    for t in topics:
        for i,tweet in enumerate(sntwitter.TwitterSearchScraper(t).get_items()):
            if i>100:
                break
            listener.on_data(tweet.content)



if __name__ == '__main__':
    main()
