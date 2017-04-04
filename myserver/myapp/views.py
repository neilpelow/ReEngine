# --- Import Libraries --- #
import json
from django import http
from django.http import StreamingHttpResponse
from django.http import JsonResponse
from django.shortcuts import render
import pandas as pd
import numpy as np
from scipy.spatial.distance import cosine
from django.conf.urls import include, url
from django.contrib import admin
from django.core import serializers
from sys import stdout


def post(request):

    def getSimilarityScore(history, similarities):
        return sum(history * similarities) / sum(similarities)

    received_json_data = json.loads(request.body, encoding="utf-8-sig")
    received_json_data = received_json_data['data']

    df = pd.DataFrame(received_json_data)
    df = df.fillna(1)
    df = pd.DataFrame(df).astype(int)

    df = pd.pivot_table(
        df, values='attending',
        index=['userId'],
        columns=['eventId'])

    df = df.reset_index()
    df = df.fillna(1)
    data_file = df.drop('userId', 1)
    # Dataframe for item vs. item similarity scores
    data_item_based_similarity = pd.DataFrame(index=data_file.columns,
                            columns=data_file.columns)

    data_item_based_similarity.reset_index()
    # Lets fill in those empty spaces with cosine similarities
    # Loop through the columns
    for column in range(0, len(data_item_based_similarity.columns)):
        # Loop through the columns for each column
        for row in range(0, len(data_item_based_similarity.columns)):
            # Fill in placeholder with cosine similarities
            data_item_based_similarity.iloc[column,row] = 1-cosine(data_file.iloc[:,column], data_file.iloc[:,row])
    # Create placeholder items for closest neighbours to an item
    data_neighbours = pd.DataFrame(index=data_item_based_similarity.columns, columns=[range(1, 11)])
    # Loop through our similarity dataframe and fill in neighbouring item names
    for column in range(0, len(data_item_based_similarity.columns)):
        data_neighbours.iloc[column, :10] = data_item_based_similarity.iloc[
            0:, column].order(ascending=False)[:10].index

    # Create a place holder matrix for similarities, and fill in the user name column.
    data_similarity = pd.DataFrame(index=df.index, columns=df.columns)
    data_similarity.iloc[:, :1] = df.iloc[:, :1]
    print(len(data_similarity.index))
    # Loop through all rows, skipping the user column, and fill with similarity scores.
    for column in range(1, len(data_similarity.index)):
        stdout.write("\r%d" % column)
        stdout.flush()
        for row in range(1, len(data_similarity.columns)):
            user = data_similarity.index[column]
            event = data_similarity.columns[row]
            # If an event has already been attended, do not recommend it.
            if df.iloc[column][row] == 1:
                data_similarity.iloc[column][row] = 0
            else:
                event_top_names = data_neighbours.loc[event][1:10]
                event_top_sims = data_item_based_similarity.ix[event].order(ascending=False)[1:10]
                user_purchases = data_file.ix[user, event_top_names]
                data_similarity.iloc[column][row] = getSimilarityScore(user_purchases, event_top_sims)
    # Get the top 6 events for each user and store in a DateFrame.
    data_recommend = pd.DataFrame(index=data_similarity.index, columns=[
        'userId', '1', '2', '3', '4', '5', '6'
    ])
    data_recommend.iloc[0:, 0] = data_similarity.iloc[:, 0]
    # Instead of top event scores, we want to see eventId numbers so they can be passed back to the app.
    for column in range(0, len(data_similarity.index)):
        data_recommend.iloc[column, 1:] = data_similarity.iloc[column, :].order(
            ascending=False).iloc[1:7, ].index.transpose()
    # Return all recommendations in response to HTTP post to be parsed on the client side.
    print(data_recommend.to_string)
    json_recommend = data_recommend.to_json(orient='index')
    print(json_recommend)
    if json_recommend is not None:
        return JsonResponse(json_recommend, content_type='json', safe=False)