import json
import tweepy
import pandas as pd
import pickle
from TweetAuthorshipPredictor import TweetAuthorshipPredictor


credentials = json.load(open('.env/twitter_credentials.json'))

consumer_key = credentials['consumer_key']
consumer_secret = credentials['consumer_secret']
access_token = credentials['access_token']
access_token_secret = credentials['access_token_secret']

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

# test = '14649582'
realDonaldTrump = '25073877'

with open('trump.pkl', 'rb') as trump:
    model = pickle.load(trump)


class TrumpStreamListener(tweepy.StreamListener):

    def on_status(self, status):
        if status.author.id_str == realDonaldTrump:
            tweet = pd.DataFrame(columns=['created_at',
                                          'favorite_count',
                                          'id_str',
                                          'in_reply_to_user_id_str',
                                          'is_retweet',
                                          'retweet_count',
                                          'source',
                                          'text'])
            tweet.loc[0] = [status.created_at,
                            status.favorite_count,
                            status.id_str,
                            status.in_reply_to_user_id_str,
                            status.retweeted,
                            status.retweet_count,
                            status.source,
                            status.text]
            prediction = predict_author(tweet)
            post_tweet(status, prediction)


def post_tweet(status, prediction):
    '''Takes a tweet, formats the response, and posts to Twitter
    INPUT: string
    OUTPUT:
    '''
    url = str('https://twitter.com/realDonaldTrump/status/' + status.id_str)
    url = ('https://twitter.com/' + status.user.screen_name +
           '/status/' + status.id_str)
    text = str(status.text)

    if prediction[0] == 0:
        tweet = ('I am {0:.0%} certain an aide wrote this:\n"{1}..."\n'
                 '@realDonaldTrump\n{2}'.
                 format(prediction[1][0][0], text[:197], url))
    else:
        tweet = ('I am {0:.0%} certain Trump wrote this:\n"{1}..."\n'
                 '@realDonaldTrump\n{2}'.
                 format(prediction[1][0][1], text[:199], url))
    api.update_status(tweet)
    print(tweet)


def predict_author(tweet):
    return model.predict(tweet)


def first_tweet(api):
    api.update_with_media('images/trump_ticker.gif',
                          status="Stay tuned!...")


def start_stream():
    while True:
        try:
            trumpstream = tweepy.Stream(auth, trumpstreamlistener)
            trumpstream.filter(follow=[realDonaldTrump])
        except:
            continue


trumpstreamlistener = TrumpStreamListener()
start_stream()
