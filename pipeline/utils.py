# utils.py
# A bag of utils functions for reproducibility.

import pandas as pd 


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
