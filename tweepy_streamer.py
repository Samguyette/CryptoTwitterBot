from tweepy import API
from tweepy import Cursor
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

import twitter_credentials

from collections import Counter
from itertools import repeat, chain

import re
import sys

import pandas as pd
import numpy as np

#Twitter client
class TwitterClient():
    def __init__(self, twitter_user=None):  #default arguemnt none, defualts as own timeline
        self.auth = TwitterAuthenticator().authenticate_twitter_app()
        self.twitter_client = API(self.auth)

        self.twitter_user = twitter_user


    def get_twitter_client_api(self):
        return self.twitter_client

    #http://docs.tweepy.org/en/v3.5.0/api.html

    def get_user_timeline_tweets(self, num_tweets):
        tweets = []
        for tweet in Cursor(self.twitter_client.user_timeline, id = self.twitter_user).items(num_tweets):
            tweets.append(tweet)

        return tweets


    def get_friend_list(self, num_friends):
        friend_list = []
        for friend in Cursor(self.twitter_client.friends, id = self.twitter_user).items(num_friends):
            friend_list.append(friend)

        return friend_list


    def get_home_timeline_tweets(self, num_tweets):
        home_timeline_tweets = []
        for tweet in Cursor(self.twitter_client.home_timeline, id = self.twitter_user).items(num_tweets):
            home_timeline_tweets.append(tweet)

        return home_timeline_tweets



#Twitter authentication
class TwitterAuthenticator():

    def authenticate_twitter_app(self):
        auth = OAuthHandler(twitter_credentials.CONSUMER_KEY, twitter_credentials.CONSUMER_SECRET)
        auth.set_access_token(twitter_credentials.ACCESS_TOKEN, twitter_credentials.ACCESS_TOKEN_SECRET)
        return auth



#Class for streaming and processing live tweets
class TwitterStreamer():

    def __init__(self):
        self.twitter_autenticator = TwitterAuthenticator()


    def stream_tweets(self, fetched_tweet_filename, hash_tag_list):
        #This handles twitter authentication and the connection to the Twitter Streaming API
        listener = TwitterListener(fetched_tweet_filename)
        auth = self.twitter_autenticator.authenticate_twitter_app()
        stream = Stream(auth, listener)

        #Filters Twitter Streams to capture data by keywords
        stream.filter(track = hash_tag_list)




#Basic listener class that prints received tweets
class TwitterListener(StreamListener):
    def __init__(self, fetched_tweet_filename):
        self.fetched_tweet_filename = fetched_tweet_filename


    def on_data(self, data):
        try:
            print(data)
            with open(self.fetched_tweet_filename, 'a') as tf:
                tf.write(data)
            return True
        except BaseException as e:
            print(str(e))

        return True

    def on_error(self, status):
        if status == 420:
            #Detects rate limmit
            return False
        print(status)


#Functionality for analyzing content from tweets
class TweetAnalyzer():

    def tweets_to_data_frame(self, tweets):
        df = pd.DataFrame(data = [tweet.text for tweet in tweets], columns = ['Tweets'])  #creates list of tweets and stores in dataframe

        #df['id'] = np.array([tweet.id for tweet in tweets])
        #df['len'] = np.array([len(tweet.text) for tweet in tweets])
        df['date'] = np.array([tweet.created_at for tweet in tweets])
        #df['source'] = np.array([tweet.source for tweet in tweets])
        #df['likes'] = np.array([tweet.favorite_count for tweet in tweets])
        #df['retweets'] = np.array([tweet.retweet_count for tweet in tweets])

        return df

    def find_most_common(self, df):
        complete_list = []
        tweetIterations = 0
        finaldate = ""
        for tweetIterations, row in df.iterrows():
            tweet = row['Tweets']
            date = row['date']

            finaldate = date
            tweet = tweet.upper()
            tweet = tweet.replace('@','')
            tweet = tweet.replace('RT','')
            tweet = tweet.replace('$CRYPTO','')
            tweet = tweet.replace('$crypto','')
            tweet = tweet.replace('$ALTS','')
            tweet = tweet.replace('$alts','')
            tweet = tweet.replace('.','')
            tweet = tweet.replace(',','')
            tweet = tweet.replace('-','')
            tweet = tweet.replace('?','')
            tweet = re.sub(r'^https?:\/\/.*[\r\n]*', '', tweet, flags=re.MULTILINE)
            tweet = tweet.replace(':','').strip()

            hash_array_mixed = [i  for i in tweet.split(" ") if i.startswith("$") ]
            hash_array = [x for x in hash_array_mixed if not any(c.isdigit() for c in x)]

            try:
                hash_array.remove("$CRYPTO")
                hash_array.remove("$crypto")
                hash_array.remove("$ALTS")
                hash_array.remove("$alts")
            except:
                pass
            #if not empty
            if hash_array:
                complete_list = complete_list + hash_array

        #organizes the list in order of most occurences
        occurrence_list = list(chain.from_iterable(repeat(i, c) for i,c in Counter(complete_list).most_common()))

        #removes duplicates but preserves order
        seen = set()
        seen_add = seen.add
        occurrence_set = [x for x in occurrence_list if not (x in seen or seen_add(x))]

        print(str(tweetIterations)+" tweets searched since: "+str(finaldate))
        print("1st: "+str(occurrence_set[0])+"\n"+"Occurrence count: "+str(complete_list.count(occurrence_set[0])))
        print("2nd: "+str(occurrence_set[1])+"\n"+"Occurrence count: "+str(complete_list.count(occurrence_set[1])))
        print("3rd: "+str(occurrence_set[2])+"\n"+"Occurrence count: "+str(complete_list.count(occurrence_set[2])))











if __name__ == "__main__":

    twitter_user_name = sys.argv[1]

    twitter_client = TwitterClient(twitter_user_name)
    tweet_analyzer = TweetAnalyzer()

    api = twitter_client.get_twitter_client_api()

    tweets = twitter_client.get_user_timeline_tweets(7000)
    #tweets = api.user_timeline(screen_name  = "bitcoin_dad", count = 2) #functions from api

    #creates data frame ds
    df = tweet_analyzer.tweets_to_data_frame(tweets)

    print("Twitter account: @"+twitter_user_name)

    #finds most common cashtag
    tweet_analyzer.find_most_common(df)









    #print(df.head(1))

    #example of printing out a variable connected to tweet
    #print(tweets[0].retweet_count)

    #prints the variables that are avalible
    #print(dir(tweets[0]))

    #hash_tag_list = ["KLKS","BTC","ETH"]
    #fetched_tweet_filename = "tweets.json"

    #twitter_client = TwitterClient('pycon')
    #print(twitter_client.get_user_timeline_tweets(1))

    #twitter_streamer = TwitterStreamer()
    #twitter_streamer.stream_tweets(fetched_tweet_filename, hash_tag_list)
