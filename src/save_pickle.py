import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from src.load_data import load_json_list, apply_date_mask
from src.vader_sentiment import apply_vader
from src.style import apply_avg_lengths, tweet_length, punctuation_columns, \
                      quoted_retweet, apply_all_caps, mention_hashtag_url
from src.tweetstorm import tweetstorm
from src.time_of_day import time_of_day
from src.part_of_speech import pos_tagging, ner_tagging
from sklearn.feature_extraction.text import TfidfVectorizer


def main():
    # Create Train, Validation, and Test sets
    X_train, X_test, y_train, y_test = data()
    X_train, X_val, y_train, y_val = train_test_split(X_train, y_train,
                                                      test_size=0.2)

    # Apply feature engineering to all X sets
    print()
    print('Feature engineering on Train data')
    X_train_feat = feature_engineering(X_train)
    print()
    print('Feature engineering on Validation data')
    X_val_feat = feature_engineering(X_val)
    print()
    print('Feature engineering on Test data')
    X_test_feat = feature_engineering(X_test)

    # # Create ner column for Name Entity Recognition
    # print()
    # print('Performing NER on Train Data')
    # X_train = named_entity_recognition(X_train)
    # print('Performing NER on Validation Data')
    # X_val = named_entity_recognition(X_val)
    # print('Performing NER on Test Data')
    # X_test = named_entity_recognition(X_test)

    # Create TF-IDF for text column
    print()
    print('TF-IDF on text column')
    tfidf_text = TfidfVectorizer(lowercase=False, token_pattern='\w+|\@\w+',
                                 norm='l2')
    X_train_tfidf = tf_idf_matrix(X_train, 'text', tfidf_text)
    X_val_tfidf = tf_idf_matrix(X_val, 'text', tfidf_text)
    X_test_tfidf = tf_idf_matrix(X_test, 'text', tfidf_text)

    # Create TF-IDF for pos column
    print()
    print('TF-IDF on pos column')
    tfidf_pos = TfidfVectorizer(ngram_range=(2, 4), lowercase=False,
                                norm='l2')
    X_train_pos = tf_idf_matrix(X_train, 'text', tfidf_pos)
    X_val_pos = tf_idf_matrix(X_val, 'text', tfidf_pos)
    X_test_pos = tf_idf_matrix(X_test, 'text', tfidf_pos)

    # Save pickle file
    output = open('data.pkl', 'wb')
    pickle.dump(X_train, output)
    pickle.dump(X_val, output)
    pickle.dump(X_test, output)

    pickle.dump(X_train_tfidf, output)
    pickle.dump(X_val_tfidf, output)
    pickle.dump(X_test_tfidf, output)

    pickle.dump(X_train_pos, output)
    pickle.dump(X_val_pos, output)
    pickle.dump(X_test_pos, output)

    pickle.dump(y_train, output)
    pickle.dump(y_val, output)
    pickle.dump(y_test, output)
    output.close()


def data():
    # =========================================================================
    # Load the data
    # =========================================================================
    print('Loading data')
    data_list = (['data/condensed_2009.json',
                  'data/condensed_2010.json',
                  'data/condensed_2011.json',
                  'data/condensed_2012.json',
                  'data/condensed_2013.json',
                  'data/condensed_2014.json',
                  'data/condensed_2015.json',
                  'data/condensed_2016.json',
                  'data/condensed_2017.json'])

    raw_data = load_json_list(data_list)

    # Look only at tweets between June 1, 2015 and March 26, 2017
    print('Masking data')
    masked_df = apply_date_mask(raw_data, 'created_at',
                                '2015-06-01', '2017-03-26')
    df = masked_df.sort_values('created_at').reset_index(drop=True)

    # =========================================================================
    # Testing
    df = df[0:15]
    # =========================================================================

    # Look only at iPhone and Android tweets
#    df = df.loc[(df['source'] == 'Twitter for iPhone') |
#                (df['source'] == 'Twitter for Android')]

    # Dummify is_reply column
    print('Dummifying is_reply column')
    df['in_reply_to_user_id_str'] = df['in_reply_to_user_id_str'].fillna(0)
    df['is_reply'] = np.where(df['in_reply_to_user_id_str'] == 0, False, True)

    # Separate data and labels
    print('Split data and labels')
    X = df.drop(['id_str', 'in_reply_to_user_id_str'], axis=1)
    y = pd.DataFrame(np.where(df['source'] == 'Twitter for Android', 1, 0))

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    return X_train, X_test, y_train, y_test


def feature_engineering(df):
    # =========================================================================
    # Feature engineering
    # =========================================================================

    # Create columns for vader sentiment
    print('calculating vader sentiment')
    df = apply_vader(df, 'text')

    # Create columns for average tweet, sentence, and word length of tweet
    print('calculating average tweet, sentence, and word length')
    df = tweet_length(df, 'text')
    df = apply_avg_lengths(df, 'text')

    # Create columns for counts of punctuation
    print('calculating punctuation counts')
    punctuation_dict = {'commas': ',', 'semicolons': ';', 'exclamations': '!',
                        'periods': '.', 'questions': '?', 'quote': '"'}

    df = punctuation_columns(df, 'text', punctuation_dict)

    # Create columns for counts of @mentions, #hashtags, and urls
    print('calculating mentions, hashtags, and url counts')
    df = mention_hashtag_url(df, 'text')

    # Create column identifying if the tweet is surrounding by quote marks
    print('calculating quoted retweet')
    df = quoted_retweet(df, 'text')

    # Create column indicating the count of fully capitalized words in a tweet
    print('calculating fully capitalized word counts')
    df = apply_all_caps(df, 'text')

    # Create column identifying if the tweet is part of a tweetstorm
    print('calculating tweetstorm')
    df = tweetstorm(df, 'text', 'source', 'created_at', 600)

    # Create column identifying the hour of the day that the tweet was posted
    print('calculating time of day')
    df = time_of_day(df, 'created_at')

    # Part of speech tagging
    print('calculating part of speech')
    df['pos'] = df['text'].apply(pos_tagging)

    return df


def named_entity_recognition(df):
    # Named Entity Recognition substitution
    print('calculating named entity recognition')
    df['ner'] = df['text'].apply(ner_tagging)
    return df


def tf_idf_matrix(df, column, tfidfvectorizer):
    '''
    Takes a DataFrame, a column of text, and a tfidfVectorizer. Creates tf-idf
    matrix and concatenates the matrices to the DataFrame
    INPUT: a DataFrame, string, tfidfVecorizer
    OUTPUT: a DataFrame
    '''

    print('calculating TF-IDF matrix')
    tfidf = tfidfvectorizer
    df_tfidf = tfidf.fit_transform(df[column])
    cols = tfidf.get_feature_names()
    df_tfidf = pd.DataFrame(df_tfidf.todense(), columns=[cols], index=df.index)
    # new_df = pd.concat([df, df_tfidf], axis=1)
    return df_tfidf


if __name__ == '__main__':
    main()