"""
* Folder - pipeline
* Folder purpose - Acts as a backend layer for Streamlit pages.
* File - run_pipeline.py
* File purpose - Execute entire pipeline
  
* Output - Datasets, models, model artifacts ready to use for Streamlit pages
"""

# Imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # Adds project root to path
# Use absolute imports from the 'pipeline' package for consistency when run from root
from pipeline import preprocess, clustering, anomaly_detection, trend_analysis, utils


# ============================================================================
# MAIN PIPELINE
# ============================================================================
def main():
    
    # ------------------------------------------------------------------------
    # STAGE 1: DATA INGESTION
    # ------------------------------------------------------------------------
    # Fetch latest active.csv : https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=csv
    raw_df = utils.fetch_dataset('data/raw/gp.csv')
    utils.save_dataset(raw_df, 'data/raw/gp.csv')
    
    # ─────────────────────────────────────────────────────────────────────────
    # raw_df COLUMNS:
    #   OBJECT_NAME, OBJECT_ID, EPOCH, MEAN_MOTION, ECCENTRICITY, INCLINATION,
    #   RA_OF_ASC_NODE, ARG_OF_PERICENTER, MEAN_ANOMALY, EPHEMERIS_TYPE,
    #   CLASSIFICATION_TYPE, NORAD_CAT_ID, ELEMENT_SET_NO, REV_AT_EPOCH,
    #   BSTAR, MEAN_MOTION_DOT, MEAN_MOTION_DDOT
    # ─────────────────────────────────────────────────────────────────────────
    
    # ------------------------------------------------------------------------
    # STAGE 2: DATA CLEANING
    # ------------------------------------------------------------------------
    # Drop missing value rows, duplicated rows
    sat_cleaned = preprocess.drop_rows(raw_df)
    
    # ------------------------------------------------------------------------
    # STAGE 3: FEATURE ENGINEERING
    # ------------------------------------------------------------------------
    # Feature engineering : Creating new features based on existing ones
    sat_engineered = preprocess.create_features(sat_cleaned)
    
    # Drop features not required by any ML models
    sat_final_engineered = utils.drop_features(sat_engineered, 
                            'OBJECT_ID', 'EPHEMERIS_TYPE', 'CLASSIFICATION_TYPE', 'ELEMENT_SET_NO', 'SAT_TYPE')
    
    # ─────────────────────────────────────────────────────────────────────────
    # sat_final_engineered COLUMNS:
    #   OBJECT_NAME, NORAD_CAT_ID, EPOCH,                    <- Identifiers
    #   MEAN_MOTION, ECCENTRICITY, INCLINATION,              <- Original TLE
    #   RA_OF_ASC_NODE, ARG_OF_PERICENTER, MEAN_ANOMALY,     <- Orbital angles
    #   REV_AT_EPOCH, BSTAR, MEAN_MOTION_DOT, MEAN_MOTION_DDOT,
    #   ORBIT_PERIOD_SEC, SEMI_MAJOR_AXIS, ORBIT_HEIGHT,     <- Derived features
    #   PERIGEE, APOGEE, ORBITAL_SPEED, AGE_SINCE_LAUNCH
    # ─────────────────────────────────────────────────────────────────────────
    
    # ------------------------------------------------------------------------
    # STAGE 4: SCALING
    # ------------------------------------------------------------------------
    # Remove columns not required for scaling and then scale the remaining columns
    df = utils.drop_features(sat_final_engineered, 'OBJECT_NAME', 'EPOCH', 'NORAD_CAT_ID')  
    scaled_df = preprocess.scale_dataset(df)
    
    # ------------------------------------------------------------------------
    # STAGE 5: CLUSTERING
    # ------------------------------------------------------------------------
    # Remove redundant features and run K-Means
    df = utils.drop_redundant_features(scaled_df)    
    sat_scaled_clustered = clustering.run_KMeans(df)
    print(df.columns)
    # ─────────────────────────────────────────────────────────────────────────
    # sat_scaled_clustered COLUMNS:
    #   (All scaled ML features) + CLUSTER                   <- Cluster label (0, 1, 2...)
    # ─────────────────────────────────────────────────────────────────────────
    
    # ------------------------------------------------------------------------
    # STAGE 6: ANOMALY DETECTION
    # ------------------------------------------------------------------------
    # Compute stats, find parameters, train Isolation Forest
    print('hi')
    df = sat_scaled_clustered.copy().drop(columns = ['AGE_SINCE_LAUNCH', 'REV_AT_EPOCH']) # Use the same features the K-Means model used (Except Age)
    cluster_size_list, sd_list = anomaly_detection.compute_basic_stats(df)

    contamination_list, n_estimator_list, max_sample_list = anomaly_detection.find_iso_paramters(sd_list, cluster_size_list)
    
    sat_unscaled_labeled, iso_forest_models = anomaly_detection.train_iso_model(df, 
                                                contamination_list, n_estimator_list, max_sample_list)
    
    # ─────────────────────────────────────────────────────────────────────────
    # sat_unscaled_labeled COLUMNS:
    #   (All scaled ML features from sat_scaled_clustered),  <- Scaled feature values
    #   CLUSTER,                                             <- Cluster label (0, 1, 2...)
    #   ANOMALY_LABEL,                                       <- 1 = Normal, -1 = Anomaly
    #   ANOMALY_SCORE                                        <- Isolation Forest decision score
    # ─────────────────────────────────────────────────────────────────────────
    
    # ------------------------------------------------------------------------
    # STAGE 7: FINAL OUTPUT : Pure anomaly df and final streamlit ready df
    # ------------------------------------------------------------------------
    
    # Compute per anomaly feature deviation
    anomaly_features_used = utils.drop_features(df, 'CLUSTER', 'ANOMALY_LABEL', 'ANOMALY_SCORE').columns
    final_anomalies = anomaly_detection.compute_anomaly_deviation_profile(sat_unscaled_labeled, anomaly_features_used)
    
    # Join cluster and anomaly labels to engineered dataset for Streamlit ready O/P
    streamlit_ready_df = sat_engineered.join(sat_unscaled_labeled[['CLUSTER', 'ANOMALY_LABEL', 'ANOMALY_SCORE']])
    utils.save_dataset(streamlit_ready_df, 'data/outputs/anomaly_clustered.csv')
    print('done')
    # Add OBJECT_NAME and NORAD_CAT_ID to final_anomalies for identification

    final_anomalies = final_anomalies.join(sat_final_engineered[['OBJECT_NAME', 'NORAD_CAT_ID']])
    # Reorder columns to put name and ID first
    cols = final_anomalies.columns.tolist()
    cols = ['OBJECT_NAME', 'NORAD_CAT_ID'] + [c for c in cols if c not in ['OBJECT_NAME', 'NORAD_CAT_ID']]
    final_anomalies = final_anomalies[cols]
    
    utils.save_dataset(final_anomalies, 'data/outputs/anomalies.csv')
    
    # ------------------------------------------------------------------------
    # STAGE 8:  : Trend analysis
    # ------------------------------------------------------------------------
    # Prepare a time series dataset
    shell_time_series = trend_analysis.prepare_time_series(streamlit_ready_df)
    
    # Apply Linear Regression for cognition trend
    activity_df, cluster_models = trend_analysis.apply_linear_reg(shell_time_series)
    
    
    # Analyze the cognition pattern overtime to generate launch risk score
    trend_summary = trend_analysis.trend_analysis(streamlit_ready_df, cluster_models)
    print(trend_summary.head())

    utils.save_dataset(trend_summary, 'data/outputs/trend_summary.csv')

    # Validation Summary
    print("\n" + "="*30)
    print("PIPELINE VALIDATION SUMMARY")
    print("="*30)
    print(f"Total Satellites processed: {len(streamlit_ready_df)}")
    print(f"Anomalies detected: {len(final_anomalies)}")
    print(f"Clusters analyzed: {streamlit_ready_df['CLUSTER'].nunique()}")
    print(f"Risk distribution: {trend_summary['LAUNCH_RISK_LEVEL'].value_counts().to_dict()}")
    print("="*30)
    print("Pipeline execution successful. All files saved to data/outputs/")
    
# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == '__main__':
    main()