"""
* Folder - pipeline
* Folder purpose - Acts as a backend layer for Streamlit pages.
* File - run_pipeline.py
* File purpose - Execute entire pipeline
  
* Output - Datasets, models, model artifacts ready to use for Streamlit pages
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # Adds project root to path
import preprocess, clustering, anomaly_detection, trend_analysis, utils


def main():
    print('Hello')
    # Fetch latest active.csv
    raw_df = utils.fetch_dataset('https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=csv')
    print('Data fetched successfully!')
    utils.save_dataset(raw_df, 'data/raw/gp.csv')
    
    
    # Drop missing value rows, duplicated rows
    cleaned_df = preprocess.drop_rows(raw_df)
    
    # Feature engineering : Creating new features based on existing once
    engineered_df = preprocess.create_features(cleaned_df)
    
    
    # Drop features not required by any ML models
    final_engineered_df = utils.drop_features(engineered_df, 
                            'OBJECT_ID', 'EPHEMERIS_TYPE', 'CLASSIFICATION_TYPE', 'ELEMENT_SET_NO')  # Adjust names if needed
    
    
    # Encode the categorical column : 'SAT_TYPE'
    df_encoded = preprocess.encode_category(final_engineered_df, 'SAT_TYPE')

    # Remove columns not required scaling and then scale the remaining columns
    df = utils.drop_features(df_encoded, 'OBJECT_NAME', 'EPOCH', 'NORAD_CAT_ID')  
    scaled_df = preprocess.scale_dataset(df)

    print(scaled_df.columns)

if __name__ == '__main__':
    main()
