"""
* Folder - pipeline
* Folder purpose - Acts as a backend layer for Streamlit pages.
* File - 03_anomaly_detection.py
* File purpose - Train and use the Isolation Forest algorithm, including : 
    1. Fetch clustered dataset. (Using 'utils' function)
    2. Select non redundant features (corr >= 0.9) (Using 'utils' function)
       and drop categorical featues (like satellite type)
    3. Compute basic stats for each cluster (cluster size and feature value deviation)
    4. Compute cluster specific Isolation Forest paramters for each cluster rows based on the basic 
       stats.
    5. Train Isolation Forest  

* Output - Trained model saved.
"""

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest


def compute_basic_stats(scaled_df):
    """
    Compute cluster size and average standard deviation across features 
    for each cluster.

    Args:
        scaled_df (DataFrame): Scaled dataframe  with 'CLUSTER' column
    
    Returns:
        cluster_size_list, sd_list
    """
    cluster_size_list = []
    sd_list = []
    value_counts = scaled_df['CLUSTER'].value_counts()
    
    # For each cluster: compute clust size and average SD
    for clust_id in sorted(value_counts.index):
        # --- clust size ---
        cluster_size_list.append(value_counts.loc[clust_id]) 
        
        # --- Average SD ---
        clust_rows = scaled_df[scaled_df['CLUSTER'] == clust_id] # filter out only this cluster satellites

        numeric_cols = clust_rows.select_dtypes(include = np.number).drop(columns=['CLUSTER']) # get numeric column names
        # Remove encoded columns 
        numeric_cols = numeric_cols.columns
        
        total_sd = 0 # Find the SD for each feature, then add the SD for the current cluster's all features
        for feature in numeric_cols:
            sd = clust_rows[feature].std()
            total_sd += sd

        avg_sd = total_sd / len(numeric_cols) 
        sd_list.append(avg_sd)
        
    return cluster_size_list, sd_list



def find_iso_paramters(clust_sd, cluster_size):
    """
    Find optimal Isolation Forest paramters for each cluster.\n
    The model paramters are : 
    1. Contamination : Portion of potential anomalies
    2. n_estimator: Number of isolation trees to use
    3. max_samples: Number of samples to consider for each tree

    Args:
        clust_sd (List): list containing avg SD for clusters
        cluster_size (List): List containing cluster size
    
    Returns:
        contamination_list, n_estimator_list, max_sample_list
    """

    contamination_list, n_estimator_list, max_sample_list = [None]*len(clust_sd), [None]*len(clust_sd), [None]*len(clust_sd)

    # 1. Contamination (based on cluster SD)

    # Step 1: Compute SD spread
    spread = max(clust_sd) - min(clust_sd)
    
    # Step 2: Choose min/max contamination based on spread
    if spread <= 0.2:
        min_cont, max_cont = 0.005, 0.03
    elif spread <= 0.6:
        min_cont, max_cont = 0.01, 0.08
    else:
        min_cont, max_cont = 0.02, 0.12
    
    # Step 3: Generate contamination values (dynamic for any k)
    selected_sd_range = np.linspace(min_cont, max_cont, len(clust_sd))
    
    # Step 4: Group clusters by SD (equal SD = equal contamination)
    unique_sds = sorted(set(clust_sd))
    sd_to_rank = {sd: i for i, sd in enumerate(unique_sds)}
    
    # Step 5: Assign contamination using grouped ranks
    for i in range(len(clust_sd)):
        rank = sd_to_rank[clust_sd[i]] # which rank does the cluster with This SD has
        contamination_list[i] = selected_sd_range[rank]

    
    # 2. n_estimators &  max_samples (based on cluster size)

    for i in range(len(cluster_size)):
        if cluster_size[i] < 100: # Small sized cluster
            n_estimator_list[i] = 70
            max_sample_list[i] = int(cluster_size[i] * 0.5)
            
        elif cluster_size[i] < 1000: # small to medium sized cluster
            n_estimator_list[i] = 150
            max_sample_list[i] = int(cluster_size[i] * 0.7)

        elif cluster_size[i] < 3000: #  medium to large sized cluster
            n_estimator_list[i] = 200
            max_sample_list[i] = int(cluster_size[i] * 0.9)
            
        else:                     # Large sized cluster
            n_estimator_list[i] = 350
            max_sample_list[i] = 1000

    return contamination_list, n_estimator_list, max_sample_list


def train_iso_model(unscaled_df, contamination, n_estimator, max_sample):
    """
    Train Isolation Forest to detect anomalies based on cluster.


    Args:
        unscaled_df (DataFrame): Unscaled dataframe with 'CLUSTER' column
        contamination (List): List of contamination values
        n_estimator (List): List of n_estimator values
        max_sample (List): List of max_sample values
    
    Returns:
        Dataframe with anomaly score and label and dictionary of models
    """

    iso_forest_models = {} # Store cluster ID: related iso model
    
    # Prepare the anomaly realted features
    unscaled_df['ANOMALY_LABEL'] = 0
    unscaled_df['ANOMALY_SCORE'] = 0.0
    for cluster_id in sorted(list(set(unscaled_df['CLUSTER']))):
        # Extract rows for this cluster ID
        cluster_rows = unscaled_df[unscaled_df['CLUSTER'] == cluster_id]
        
        # Skip tiny clusters -> auto flag as anomalies
        if len(cluster_rows) < 3:
            unscaled_df.loc[unscaled_df['CLUSTER']== cluster_id, 'ANOMALY_LABEL'] = -1
            unscaled_df.loc[unscaled_df['CLUSTER']== cluster_id, 'ANOMALY_SCORE'] = -0.5
            continue
        
        iso_model = IsolationForest(n_estimators=n_estimator[cluster_id], 
                                   max_samples=max_sample[cluster_id],
                                   contamination=contamination[cluster_id],
                                   max_features=1.0, # Consider all features in a tree
                                   random_state=101)
        # Train the model
        iso_model.fit(cluster_rows.drop(columns=['CLUSTER', 'ANOMALY_LABEL', 'ANOMALY_SCORE']))
        iso_forest_models[cluster_id] = iso_model # Save the model to the dictionary
        
    # Save the iso model dictionary into joblib format
    joblib.dump(iso_forest_models, 'data/models/anomalies.joblib')

        
    for cluster_id, model in iso_forest_models.items():
            # Select all rows belonging to this cluster
            mask = unscaled_df['CLUSTER'] == cluster_id

            # Extract necessary features (features + rows belonging to the cluster)
            features = unscaled_df.loc[mask].drop(columns=['CLUSTER', 'ANOMALY_LABEL', 'ANOMALY_SCORE'])

            # Predict using model trained on exact features
            labels = model.predict(features) 
            score = model.decision_function(features)

            # Store the results back to unscaled DF
            unscaled_df.loc[mask, 'ANOMALY_LABEL'] = labels
            unscaled_df.loc[mask, 'ANOMALY_SCORE'] = score

    return unscaled_df, iso_forest_models
