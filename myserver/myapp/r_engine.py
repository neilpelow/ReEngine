from django.shortcuts import render

# --- Import Libraries --- #
import json
from django import http
from django.http import StreamingHttpResponse
import pandas as pd
import numpy as np
from scipy.spatial.distance import cosine
from django.conf.urls import include, url
from django.contrib import admin


def post(request):
    #received_json_data = json.loads(request.body, encoding="utf-8-sig")
    #received_json_data = received_json_data['data']

    #df = pd.DataFrame(received_json_data)
    df = pd.read_json('/Users/neilpelow/Desktop/ReEngine/myserver/myapp/users.json')
    df = df.fillna(1)
    df = pd.DataFrame(df).astype(int)

    df = pd.pivot_table(
        df, values='attending',
        index=['userId'],  # these stay as columns; will fail silently if any of these cols have null values
        columns=['eventId'])#.astype(int)  # data values in this column become their own column

    df = df.reset_index()
    df = df.fillna(1)
    # --- Start Item Based Recommendations --- #
    # Drop any column named "userId"
    data_file = df.drop('userId', 1)
    print("This is the data_file DataFrame")
    print(data_file)
    data_file = data_file.reset_index()
    # Create a placeholder dataframe listing item vs. item
    data_ibs = pd.DataFrame(index=data_file.columns,
                            columns=data_file.columns)
    data_ibs = data_ibs.fillna(0)
    print(data_ibs)
    # Lets fill in those empty spaces with cosine similarities
    # Loop through the columns
    for i in range(0, len(data_ibs.columns)):
        # Loop through the columns for each column
        for j in range(0, len(data_ibs.columns)):
            # Fill in placeholder with cosine similarities
            data_ibs.ix[i, j] = 1 - cosine(data_file.ix[:, i], data_file.ix[:, j])
            # data_ibs.ix[i,j] = 1-cosine(data_germany.ix[:,i],data_germany.ix[:,j])
    # Create placeholder items for closest neighbours to an item
    data_neighbours = pd.DataFrame(index=data_ibs.columns, columns=[range(1, 11)])
    # Loop through our similarity dataframe and fill in neighbouring item names
    for i in range(0, len(data_ibs.columns)):
        data_neighbours.ix[i, :10] = data_ibs.ix[
            0:, i].order(ascending=False)[:10].index

    # --- End Item Based Recommendations --- #
    # --- Start User Based Recommendations --- #
    # Helper function to get similarity scores

    def getScore(history, similarities):
        return sum(history * similarities) / sum(similarities)

    # Create a place holder matrix for similarities, and fill in the user name column
    data_sims = pd.DataFrame(index=df.index, columns=df.columns)
    data_sims.ix[:, :1] = df.ix[:, :1]
    print(data_sims)
    print(len(data_sims.index))
    # Loop through all rows, skip the user column, and fill with similarity scores
    for i in range(1, len(data_sims.index)):  # up-down
        for j in range(1, len(data_sims.columns)):  # left-right
            user = data_sims.index[i]
            print(user)
            event = data_sims.columns[j]
            if df.ix[i][j] == 1:
                data_sims.ix[i][j] = 0
            else:
                event_top_names = data_neighbours.loc[event][1:10]
                event_top_sims = data_ibs.loc[event].order(ascending=False)[1:10]
                user_purchases = data_file.loc[user, event_top_names]
                data_sims.ix[i][j] = getScore(user_purchases, event_top_sims)
    # Get the top 6 events for each user. Stored in a DateFrame. 
    data_recommend = pd.DataFrame(index=data_sims.index, columns=[
        'userId', '1', '2', '3', '4', '5', '6'
    ])
    data_recommend.ix[0:, 0] = data_sims.ix[:, 0]
    print(data_sims)
    # Instead of top event scores, we want to see eventId numbers.
    for i in range(0, len(data_sims.index)):
        data_recommend.ix[i, 1:] = data_sims.ix[i, :].order(
            ascending=False).ix[1:7, ].index.transpose()
    # Return all recommendations in response to HTTP post.
    return data_recommend.to_string

if __name__ == "__main__":
    post('blah')