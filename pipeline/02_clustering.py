"""
* Folder - pipeline
* Folder purpose - Acts as a backend layer for Streamlit pages.
* File - 02_clustering.py
* File purpose - Train and use the K-Means algorithm, including : 
    1. Fetch preprocessed dataset. (Using 'utils' function)
    2. Select non redundant features (corr >= 0.9) (Using 'utils' function)
    3. Train K-Means model (k=5)

* Output - 'sat_scaled_labeled.csv' and 'sat_unscaled_labeled.csv' from a series of functions.
"""

# Required libraries for this component / file
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans


