"""
Data Loader Component for SpaceDebrisRadar.AI
Centralized data loading with Streamlit caching for efficient access.
"""

import streamlit as st
import pandas as pd
import numpy as np
import os

# Data directory path
_current_dir = os.path.dirname(os.path.abspath(__file__))
_app_dir = os.path.dirname(_current_dir)
_project_root = os.path.dirname(_app_dir)
DATA_DIR = os.path.join(_project_root, 'data', 'outputs')


@st.cache_data(ttl=3600)
def load_satellite_data():
    """Load the main satellite dataset with cluster and anomaly labels."""
    data_path = os.path.join(DATA_DIR, 'anomaly_clustered.csv')
    df = pd.read_csv(data_path)
    df['EPOCH'] = pd.to_datetime(df['EPOCH'])
    return df


@st.cache_data(ttl=3600)
def load_trend_summary():
    """Load pre-computed trend analysis summary."""
    data_path = os.path.join(DATA_DIR, 'trend_summary.csv')
    df = pd.read_csv(data_path)
    df['LAUNCH_RISK_LEVEL'] = df['LAUNCH_RISK_LEVEL'].fillna('N/A')
    return df


@st.cache_data(ttl=3600)
def load_anomalies():
    """Load pre-computed anomaly data with deviation profiles."""
    data_path = os.path.join(DATA_DIR, 'anomalies.csv')
    df = pd.read_csv(data_path)
    return df


@st.cache_data(ttl=3600)
def get_system_metrics():
    """Get high-level system metrics for the overview page."""
    df = load_satellite_data()
    trend_summary = load_trend_summary()
    
    total_satellites = len(df)
    total_shells = df['CLUSTER'].nunique()
    total_anomalies = len(df[df['ANOMALY_LABEL'] == -1])
    
    risk_levels = {'Low': 1, 'Moderate': 2, 'High': 3, 'N/A': 0}
    weighted_risk = 0
    total_weight = 0
    
    for _, row in trend_summary.iterrows():
        cluster_id = row['CLUSTER_ID']
        risk = row['LAUNCH_RISK_LEVEL']
        if risk in risk_levels and risk != 'N/A':
            cluster_count = len(df[df['CLUSTER'] == cluster_id])
            weighted_risk += risk_levels[risk] * cluster_count
            total_weight += cluster_count
    
    if total_weight > 0:
        avg_risk_score = weighted_risk / total_weight
        if avg_risk_score >= 2.5:
            overall_risk = 'High'
        elif avg_risk_score >= 1.5:
            overall_risk = 'Moderate'
        else:
            overall_risk = 'Low'
    else:
        overall_risk = 'N/A'
    
    return {
        'total_satellites': total_satellites,
        'total_shells': total_shells,
        'total_anomalies': total_anomalies,
        'overall_risk': overall_risk,
        'anomaly_rate': round(total_anomalies / total_satellites * 100, 1)
    }


@st.cache_data(ttl=3600)
def get_cluster_summary():
    """Get per-cluster summary statistics."""
    df = load_satellite_data()
    trend_summary = load_trend_summary()
    
    cluster_stats = []
    for cluster_id in sorted(df['CLUSTER'].unique()):
        cluster_df = df[df['CLUSTER'] == cluster_id]
        trend_row = trend_summary[trend_summary['CLUSTER_ID'] == cluster_id]
        
        if len(trend_row) > 0:
            trend_type = trend_row['TREND_TYPE'].values[0]
            risk_level = trend_row['LAUNCH_RISK_LEVEL'].values[0]
            slope = trend_row['SLOPE'].values[0]
            activity_fraction = trend_row['CURRENT_ACTIVITY_FRACTION'].values[0]
        else:
            trend_type = 'Unknown'
            risk_level = 'N/A'
            slope = 0
            activity_fraction = 0
        
        stats = {
            'cluster_id': cluster_id,
            'satellite_count': len(cluster_df),
            'anomaly_count': len(cluster_df[cluster_df['ANOMALY_LABEL'] == -1]),
            'anomaly_rate': round(len(cluster_df[cluster_df['ANOMALY_LABEL'] == -1]) / len(cluster_df) * 100, 1),
            
            # Altitude details
            'min_altitude': round(cluster_df['ORBIT_HEIGHT'].min(), 1),
            'max_altitude': round(cluster_df['ORBIT_HEIGHT'].max(), 1),
            'avg_altitude': round(cluster_df['ORBIT_HEIGHT'].mean(), 1),
            'altitude_span': round(cluster_df['ORBIT_HEIGHT'].max() - cluster_df['ORBIT_HEIGHT'].min(), 1),
            
            # Speed details (km/s)
            'min_speed': round(cluster_df['ORBITAL_SPEED'].min(), 2),
            'max_speed': round(cluster_df['ORBITAL_SPEED'].max(), 2),
            'avg_speed': round(cluster_df['ORBITAL_SPEED'].mean(), 2),
            
            # Period details (converted to minutes)
            'min_period': round(cluster_df['ORBIT_PERIOD_SEC'].min() / 60, 1),
            'max_period': round(cluster_df['ORBIT_PERIOD_SEC'].max() / 60, 1),
            'avg_period': round(cluster_df['ORBIT_PERIOD_SEC'].mean() / 60, 1),
            
            # Geometry
            'min_inclination': round(cluster_df['INCLINATION'].min(), 1),
            'max_inclination': round(cluster_df['INCLINATION'].max(), 1),
            'avg_inclination': round(cluster_df['INCLINATION'].mean(), 1),
            'avg_eccentricity': round(cluster_df['ECCENTRICITY'].mean(), 4),
            
            'trend_type': trend_type,
            'risk_level': risk_level,
            'slope': slope,
            'activity_fraction': round(activity_fraction * 100, 1)
        }
        cluster_stats.append(stats)
    
    return pd.DataFrame(cluster_stats)


@st.cache_data(ttl=3600)
def get_anomaly_data():
    """Get all anomalous satellites with deviation profiles."""
    return load_anomalies()


def get_anomalies_by_cluster(cluster_id=None):
    """Get anomalies filtered by cluster."""
    anomalies = get_anomaly_data()
    if cluster_id is not None:
        anomalies = anomalies[anomalies['CLUSTER'] == cluster_id]
    return anomalies


def get_top_deviating_features_summary():
    """Get summary of most common deviating features."""
    anomalies = get_anomaly_data()
    return anomalies['TOP_DEVIATING_FEATURE'].value_counts()


def clear_cache():
    """Clear all memoized data to force reload from disk."""
    st.cache_data.clear()

