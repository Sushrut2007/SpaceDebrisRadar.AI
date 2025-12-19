"""
* Folder - pipeline
* Folder purpose - Acts as a backend layer for Streamlit pages.
* File - run_pipeline.py
* File purpose - Execute entire pipeline
  
* Output - Datasets, models, model artifacts ready to use for Streamlit pages
"""

from pipeline import preprocess, clustering, anomaly_detection, trend_analysis, utils



