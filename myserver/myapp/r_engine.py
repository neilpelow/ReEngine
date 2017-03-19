# --- Import Libraries --- #
import json
from django import http
from django.http import StreamingHttpResponse
import pandas as pd
from scipy.spatial.distance import cosine
from django.conf.urls import include, url
from django.contrib import admin

@csrf_exempt
def POST(request):
    
    received_json_data=json.loads(request.body)
    data = pd.read_json(received_json_data)
    # --- Start Item Based Recommendations --- #
    # Drop any column named "user"
    data_file = data.drop('user', 1)
    # Create a placeholder dataframe listing item vs. item
    data_ibs = pd.DataFrame(index=data_file.columns,
                            columns=data_file.columns)
    # Lets fill in those empty spaces with cosine similarities
    # Loop through the columns
    for i in range(0, len(data_ibs.columns)):
        # Loop through the columns for each column
        for j in range(0, len(data_ibs.columns)):
            # Fill in placeholder with cosine similarities
            data_ibs.ix[i, j] = 1 - \
                cosine(data_file.ix[:, i], data_file.ix[:, j])
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
    # Create a place holder matrix for similarities, and fill in the user name
    # column
    data_sims = pd.DataFrame(index=data.index, columns=data.columns)
    data_sims.ix[:, :1] = data.ix[:, :1]
    #Loop through all rows, skip the user column, and fill with similarity scores
    for i in range(0, len(data_sims.index)):
        for j in range(1, len(data_sims.columns)):
            user = data_sims.index[i]
            product = data_sims.columns[j]
            if data.ix[i][j] == 1:
                data_sims.ix[i][j] = 0
            else:
                product_top_names = data_neighbours.ix[product][1:10]
                product_top_sims = data_ibs.ix[
                    product].order(ascending=False)[1:10]
                user_purchases = data_file.ix[user, product_top_names]
                data_sims.ix[i][j] = getScore(user_purchases, product_top_sims)
    # Get the top songs
    data_recommend = pd.DataFrame(index=data_sims.index, columns=[
        'user', '1', '2', '3', '4', '5', '6'
        ])
    data_recommend.ix[0:, 0] = data_sims.ix[:, 0]
    # Instead of top event scores, we want to see eventId numbers.
    for i in range(0, len(data_sims.index)):
        data_recommend.ix[i, 1:] = data_sims.ix[i, :].order(
            ascending=False).ix[1:7, ].index.transpose()
    # Return all recommendations
    return data_recommend.to_string