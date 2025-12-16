"""
* Folder - pipeline
* Folder purpose - Acts as a backend layer for Streamlit pages.
* File - 04_trend_analysis.py
* File purpose - Train and use the Linear Regression algorithm, including : 
    1. Fetch anomaly_clustered dataset. (Using 'utils' function)
    2. Prepare a dummy yet simple and meaningful time series dataset
       In which: features = ['Epoch', 'Cluster ID', 'Satellite count in each cluster  for that epoch']        
    3. Train a regression model for each cluster (with bit of a complex yet simple logic)
    4. Prepare final launch risk summary  

* Output - Trained model saved and final launch risk summary.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def prepare_time_series(df):
    """
    Prepare a simple, dummy yet meaningful satellite time series dataset.\n
    Finds satellite count for each epoch in available clusters.

    Args:
        df (DataFrame): clustered_anomaly dataframe
    
    Returns:
        shell_time_series 
    """
    
    # Extract necessary columns 
    df = df[['EPOCH', 'NORAD_CAT_ID', 'CLUSTER']] 
    # convert Epoch to a datetime object and extract only the data
    df['EPOCH'] = pd.to_datetime(df['EPOCH'])
    df['EPOCH'] = df['EPOCH'].dt.floor('D')

    shell_time_series = df.groupby(['EPOCH', 'CLUSTER']).size().reset_index(name='SATELLITE_COUNT')

    return shell_time_series


def trend_analysis(shell_time_series):
    """
    Train a Linear regression model for satellite traffic risk analysis for each cluster.\n
    If regresion cannto be applied to a cluster, apply default slope and intercept (0 or None).

    Args:
        shell_time_series (DataFrame): Satellite dummy time series dataframe
    
    Returns:
        activity_df, cluster_models
    """

    cluster_models = [] # Store cluster specific model information
    activity_df = pd.DataFrame() # Store cluster data with fraction for each day

    for cluster in range(shell_time_series['CLUSTER'].nunique()):
        # Filter rows for the current cluster
        cluster_rows = shell_time_series[shell_time_series['CLUSTER'] == cluster].copy()
        

        # Convert EPOCH into numeric days starting from the earliest date
        cluster_rows['EPOCH_NUM'] = (
            (cluster_rows["EPOCH"] - cluster_rows["EPOCH"].min()).dt.total_seconds() / (24 * 3600)
        )

        # Compute activity fraction for regression target
        total_updates = cluster_rows['SATELLITE_COUNT'].sum()
        cluster_rows['ACTIVITY_FRACTION'] = cluster_rows['SATELLITE_COUNT'] / total_updates

        # Add the cluster rows to the activity_df
        pd.concat([activity_df, cluster_rows])

        
        # Skip regressing clusters that have fewer than 3 data points
        if len(cluster_rows) < 3:
            current_fraction = round(cluster_rows['ACTIVITY_FRACTION'].iloc[-1], 5)

            cluster_models.append({
                'Cluster': cluster,
                'Model': None,
                'Slope': 0,
                'Intercept': None,
                'Current activity fraction': current_fraction
            })
            continue
        
        # Set up regression inputs
        X = cluster_rows[['EPOCH_NUM']]
        y = cluster_rows[['ACTIVITY_FRACTION']]

        # Fit the regression model
        model = LinearRegression()
        model.fit(X, y)

        # Extract slope, intercept and latest fraction
        slope = round(model.coef_[0][0], 5)
        intercept = round(model.intercept_[0], 5)
        current_fraction = round(y.iloc[-1].values[0], 5)
        
        # Store model details
        cluster_models.append({
            'Cluster': cluster,
            'Model': model,
            'Slope': slope,
            'Intercept': intercept,
            'Current activity fraction': current_fraction
        })

    # Reset activity_df index
    activity_df = activity_df.reset_index(drop=True)