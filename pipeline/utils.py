# utils.py
# A bag of utils functions for reproducibility.

import pandas as pd 
from sklearn.preprocessing import OneHotEncoder


#----------------------
# CSV FILE RELATED HELPERS
#----------------------

def fetch_dataset(data_path):
    """ 
     Fetch / load  dataset from existing directory CSV file or HTTPS link.

    Args:
        data_path (String): CSV file location / HTTPS link of the dataset
    
    Returns: CSV dataset
    """
    df = pd.read_csv(data_path, low_memory=False)
    return df


def save_dataset(df, data_path):
    """ 
     Save the dataset to the given directory path in the form of CSV.

    Args:
        df (DataFrame): Dataframe to save as CSV
        data_path (String): CSV file location / HTTPS link of the dataset

    Returns: None 
    """

    df.to_csv(data_path, index=False)
    

#----------------------
# DATASET FEATURE HANDLING HELPERS
#----------------------

def drop_features(df, *args):
    """
    Drop features in the dataset.

    Args:
        df (DataFrame): Satellite dataset with atleast one feature
        *args (tuple): a tuple of feature names to drop
    
    Returns: Dataset with dropped features
    """

    return df.drop(columns = args)


