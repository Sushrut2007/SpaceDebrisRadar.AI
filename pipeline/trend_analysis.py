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
import utils
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
    df = df[['EPOCH', 'NORAD_CAT_ID', 'CLUSTER']].copy() 
    # convert Epoch to a datetime object and extract only the date
    df['EPOCH'] = pd.to_datetime(df['EPOCH'])
    df['EPOCH'] = df['EPOCH'].dt.floor('D')

    shell_time_series = df.groupby(['EPOCH', 'CLUSTER']).size().reset_index(name='SATELLITE_COUNT')

    return shell_time_series


def apply_linear_reg(shell_time_series):
    """
    Train a Linear regression model for satellite traffic risk analysis for each cluster.\n
    If regression cannot be applied to a cluster, apply default slope and intercept (0 or None).

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
        activity_df = pd.concat([activity_df, cluster_rows])

        
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

    return activity_df, cluster_models

def trend_analysis(activity_df, cluster_models):
    """
    Analyze the shell activity and potential anomalies to generate final launch risk score.\n
    The criteria used for the risk score : 
    Define trend type based on 'relative' slope in each cluster : 
        
        normalized = slope / max_slope (bewteen  0 to 1)
        
        > 0.70     ΓåÆ Strong Rising
        0.30ΓÇô0.70  ΓåÆ Moderate Rising
        0.10ΓÇô0.30  ΓåÆ Mild Rising
        -0.10ΓÇô0.10 ΓåÆ Flat
        < -0.10    ΓåÆ Calming
    
    Launch Risk Rules (Enhanced: Trend + Activity + Anomaly Stability)

    1) Base Risk (from trend + activity):
        High      ΓåÆ slope ΓëÑ 0.30  AND  activity > 0.30
        Moderate  ΓåÆ slope 0.00ΓÇô0.29  OR  activity 0.10ΓÇô0.35
        Low       ΓåÆ activity < 0.10  OR  trend flat/calming

    2) Anomaly Stability Modifier:
        anomaly_rate > 0.15  ΓåÆ increase risk by one level
        anomaly_rate < 0.05  ΓåÆ decrease risk if borderline
        otherwise            ΓåÆ keep base risk same

    Final Risk = Base Risk adjusted by anomaly stability.

    Args:
        activity_df (DataFrame): Activity df including the activity fraction 
        cluster_models (Dictionary): Regression based information for each cluster
    
    Returns:
        trend_summary
    """
    # Define the final trend summary features
    trend_summary = pd.DataFrame(columns=['CLUSTER_ID', 'SLOPE', 'CURRENT_ACTIVITY_FRACTION', 'TREND_TYPE', 'LAUNCH_RISK_LEVEL'])

    # Find minimum and maximum model slopes across clusters
    min_slope = min(d['Slope'] for d in cluster_models)
    max_slope = max(d['Slope'] for d in cluster_models)
    
    df = utils.fetch_dataset('data/outputs/anomaly_clustered.csv')

    
    # Use the clustered_model to add the cluster related information obtained through regression
    for item in cluster_models:
        cluster = item['Cluster']
        slope = item['Slope']
        current_fraction = item['Current activity fraction']

        if item['Model'] is None:
            trend_type = 'No Trend'
            base_risk_level = 'N/A'

            trend_summary.loc[len(trend_summary)] = [cluster, slope, current_fraction, trend_type, base_risk_level]
            continue
        # 1. Relative slope strength/trend
        # Scale the relative strength betwwen 0 to 1
        normalized = (slope - min_slope) / (max_slope - min_slope) 

        # Trend classification
        if normalized > 0.70:
            trend_type = 'Strong Rising'
        elif normalized >= 0.30:
            trend_type = 'Moderate Rising'
        elif normalized >= 0.10:
            trend_type = 'Mild Rising'
        elif normalized >= -0.10:
            trend_type = 'Flat'
        else:
            trend_type = 'Calming'


        # 2. Launch risk score classification -> Base risk
        if (normalized >0.3) and (current_fraction >0.3): # Strong & Moderate rising
            base_risk_level = 'High'
        elif (0.29>=normalized>=0.0) and (0.35>=current_fraction>=0.0): # Mild rising / any rising trend
            base_risk_level = 'Moderate'
        else: # Flat / Stable / Calming
            base_risk_level = 'Low'
            
        # 3. Compute anomaly rate and find final risk score
        cluster_data = df[df['CLUSTER'] == cluster]
        total_sats = len(cluster_data)
        total_anomalies = len(cluster_data[cluster_data['ANOMALY_LABEL'] == -1])

        anomaly_rate =  total_anomalies / total_sats # Compute anomaly rate

        # Adjust risk based on the anomaly rate
        if anomaly_rate > 0.15:
            # Increase risk by one level
            if base_risk_level == 'Low':
                final_risk_level = 'Moderate'
            elif base_risk_level == 'Moderate':
                final_risk_level = 'High'
            else:
                final_risk_level = base_risk_level
        
        elif anomaly_rate < 0.05:
            # Decrease risk by one level
            if base_risk_level == 'High':
                final_risk_level = 'Moderate'
            elif base_risk_level == 'Moderate':
                final_risk_level = 'Low'
            else:
                final_risk_level = base_risk_level
        else:
            final_risk_level = base_risk_level

        # 4. Append row data
        trend_summary.loc[len(trend_summary)] = [cluster, slope, current_fraction, trend_type, final_risk_level]

    return trend_summary
    
    
