"""
* Folder - pipeline
* Folder purpose - Acts as a backend layer for Streamlit pages.
* File - 02_clustering.py
* File purpose - Train and use the K-Means algorithm, including : 
    1. Fetch preprocessed dataset. (Using 'utils' function)
    2. Select non redundant features (corr >= 0.9) (Using 'utils' function)
    3. Train K-Means model (k=5)

* Output - Trained model saved.
"""

# Required libraries for this component / file
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
import joblib
from pipeline.utils import fetch_dataset



def run_KMeans(df):
    """
    Train KMeans algorithm to cluster related rows into groups of similar satellites.\n
    Uses: k = 5\n
    Also saves the KMeans model for future use.

    Args:
        df (DataFrame): Dataframe with 'clusterable' columns
    
    Returns: 
        Dataframe with added 'CLUSTER' column
    """

    model = KMeans(n_clusters=5, random_state=101)
    # Train and test the model
    cluster_labels = model.fit_predict(df)

    # Make a seperate column
    df['CLUSTER'] = cluster_labels

    # Save the model as .joblib
    joblib.dump(model, '../models/clustering.joblib')

    return df