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
# HELPER FUNCTIONS FOR NICE OUTPUT
# ============================================================================
def print_header(title):
    """Print a styled header for pipeline start."""
    print("\n" + "=" * 70)
    print(f"{'🚀 ' + title + ' 🚀':^70}")
    print("=" * 70)

def print_stage(stage_num, title):
    """Print a styled stage header."""
    print(f"\n{'─' * 70}")
    print(f"  📌 STAGE {stage_num}: {title}")
    print(f"{'─' * 70}")

def print_success(message):
    """Print a success message."""
    print(f"  ✅ {message}")

def print_info(message):
    """Print an info message."""
    print(f"  ℹ️  {message}")

def print_stats(label, value):
    """Print a stat with label."""
    print(f"     • {label}: {value}")

def print_footer():
    """Print pipeline completion footer."""
    print("\n" + "=" * 70)
    print(f"{'🎉 PIPELINE COMPLETED SUCCESSFULLY 🎉':^70}")
    print("=" * 70 + "\n")


# ============================================================================
# MAIN PIPELINE
# ============================================================================
def main():
    print_header("SPACE DEBRIS ANALYSIS PIPELINE")
    
    # ------------------------------------------------------------------------
    # STAGE 1: DATA INGESTION
    # ------------------------------------------------------------------------
    print_stage(1, "DATA INGESTION")
    # Fetch latest active.csv : https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=csv
    raw_df = utils.fetch_dataset('https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=csv')
    utils.save_dataset(raw_df, 'data/raw/gp.csv')
    print_success("Dataset fetched and saved")
    print_stats("Total records loaded", f"{len(raw_df):,}")
    print_stats("Total features", raw_df.shape[1])
    
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
    print_stage(2, "DATA CLEANING")
    # Drop missing value rows, duplicated rows
    sat_cleaned = preprocess.drop_rows(raw_df)
    print_success("Missing values and duplicates removed")
    print_stats("Records before", f"{len(raw_df):,}")
    print_stats("Records after", f"{len(sat_cleaned):,}")
    print_stats("Records dropped", f"{len(raw_df) - len(sat_cleaned):,}")
    
    # ------------------------------------------------------------------------
    # STAGE 3: FEATURE ENGINEERING
    # ------------------------------------------------------------------------
    print_stage(3, "FEATURE ENGINEERING")
    # Feature engineering : Creating new features based on existing ones
    sat_engineered = preprocess.create_features(sat_cleaned)
    print_success("New features created")
    print_stats("Features before", sat_cleaned.shape[1])
    print_stats("Features after", sat_engineered.shape[1])
    
    # Drop features not required by any ML models
    sat_final_engineered = utils.drop_features(sat_engineered, 
                            'OBJECT_ID', 'EPHEMERIS_TYPE', 'CLASSIFICATION_TYPE', 'ELEMENT_SET_NO', 'SAT_TYPE')
    print_success("Unnecessary features dropped")
    
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
    print_stage(4, "SCALING")
    # Remove columns not required for scaling and then scale the remaining columns
    df = utils.drop_features(sat_final_engineered, 'OBJECT_NAME', 'EPOCH', 'NORAD_CAT_ID')  
    scaled_df = preprocess.scale_dataset(df)
    print_success("Dataset scaled successfully")
    print_stats("Scaled features", scaled_df.shape[1])
    
    # ------------------------------------------------------------------------
    # STAGE 5: CLUSTERING
    # ------------------------------------------------------------------------
    print_stage(5, "CLUSTERING")
    # Remove redundant features and run K-Means
    df = utils.drop_redundant_features(scaled_df)
    sat_scaled_clustered = clustering.run_KMeans(df)
    print_success("K-Means clustering completed")
    print_stats("Number of clusters", sat_scaled_clustered['CLUSTER'].nunique())
    print_info("Cluster distribution:")
    for cluster, count in sat_scaled_clustered['CLUSTER'].value_counts().sort_index().items():
        print(f"       Cluster {cluster}: {count:,} satellites")
    
    # ─────────────────────────────────────────────────────────────────────────
    # sat_scaled_clustered COLUMNS:
    #   (All scaled ML features) + CLUSTER                   <- Cluster label (0, 1, 2...)
    # ─────────────────────────────────────────────────────────────────────────
    
    # ------------------------------------------------------------------------
    # STAGE 6: ANOMALY DETECTION
    # ------------------------------------------------------------------------
    print_stage(6, "ANOMALY DETECTION")
    # Compute stats, find parameters, train Isolation Forest
    df = sat_scaled_clustered.copy() # Use the same features the K-Means model used
    cluster_size_list, sd_list = anomaly_detection.compute_basic_stats(df)
    print_success("Basic statistics computed")
    
    contamination_list, n_estimator_list, max_sample_list = anomaly_detection.find_iso_paramters(sd_list, cluster_size_list)
    print_success("Isolation Forest parameters determined")
    
    sat_unscaled_labeled, iso_forest_models = anomaly_detection.train_iso_model(df, 
                                                contamination_list, n_estimator_list, max_sample_list)
    print_success("Isolation Forest models trained")
    
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
    print_stage(7, "FINAL OUTPUT GENERATION")
    # Compute per anomaly feature deviation
    anomaly_features_used = utils.drop_features(df, 'CLUSTER', 'ANOMALY_LABEL', 'ANOMALY_SCORE').columns
    final_anomalies = anomaly_detection.compute_anomaly_deviation_profile(sat_unscaled_labeled, anomaly_features_used)
    print_success("Anomaly deviation profiles computed")
    
    # Join cluster and anomaly labels to engineered dataset for Streamlit ready O/P
    streamlit_ready_df = sat_engineered.join(sat_unscaled_labeled[['CLUSTER', 'ANOMALY_LABEL', 'ANOMALY_SCORE']])
    utils.save_dataset(streamlit_ready_df, 'data/outputs/anomaly_clustered.csv')
    
    # Add OBJECT_NAME and NORAD_CAT_ID to final_anomalies for identification

    final_anomalies = final_anomalies.join(sat_final_engineered[['OBJECT_NAME', 'NORAD_CAT_ID']])
    # Reorder columns to put name and ID first
    cols = final_anomalies.columns.tolist()
    cols = ['OBJECT_NAME', 'NORAD_CAT_ID'] + [c for c in cols if c not in ['OBJECT_NAME', 'NORAD_CAT_ID']]
    final_anomalies = final_anomalies[cols]
    
    utils.save_dataset(final_anomalies, 'data/outputs/anomalies.csv')
    
    print_success("Streamlit-ready dataset prepared")

    # Check if anomalies have extreme values
    normal = sat_unscaled_labeled[sat_unscaled_labeled['ANOMALY_LABEL'] == 1]
    anomalies = sat_unscaled_labeled[sat_unscaled_labeled['ANOMALY_LABEL'] == -1]

    print_info("MEAN_MOTION Analysis:")
    print_stats("Normal range", f"{normal['MEAN_MOTION'].min():.4f} - {normal['MEAN_MOTION'].max():.4f}")
    print_stats("Anomaly range", f"{anomalies['MEAN_MOTION'].min():.4f} - {anomalies['MEAN_MOTION'].max():.4f}")
    
    print_info("Detection Summary:")
    print_stats("Total satellites", f"{len(sat_unscaled_labeled):,}")
    print_stats("Normal satellites", f"{len(normal):,}")
    print_stats("Anomalies detected", f"{len(anomalies):,}")
    print_stats("Anomaly percentage", f"{(len(anomalies)/len(sat_unscaled_labeled)*100):.2f}%")
    
    print_info("Top Deviating Features:")
    for feature, count in final_anomalies['TOP_DEVIATING_FEATURE'].value_counts().head(5).items():
        print(f"       {feature}: {count:,}")
    
    print_footer()
    
    # ------------------------------------------------------------------------
    # STAGE 8:  : Trend analysis
    # ------------------------------------------------------------------------
    # Prepare a time series dataset
    shell_time_series = trend_analysis.prepare_time_series(streamlit_ready_df)
    
    # Apply Linear Regression for cognition trend
    activity_df, cluster_models = trend_analysis.apply_linear_reg(shell_time_series)
    
    
    # Analyze the cognition pattern overtime to generate launch risk score
    trend_summary = trend_analysis.trend_analysis(streamlit_ready_df, cluster_models)

    utils.save_dataset(trend_summary, 'data/outputs/trend_summary.csv')
    
    print(trend_summary.head())
    
    
# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == '__main__':
    main()