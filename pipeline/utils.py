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


def encode_category(df, col):
    """
    Encode categorical features using OneHotEncoder.

    Args:
        df (DataFrame): A dataframe containing categorical feature
        col (String): Feature to OneHotEncode.
    
    Returns: Dataframe with encoded feature, Encoder.pkl
    """

    # Fit and transform
    encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    X_encoded = encoder.fit_transform(df[[feature]])

    # Get actual category names
    encoded_cols = encoder.get_feature_names_out([feature])

    # Convert to DataFrame with proper column names
    df_encoded = pd.concat([df.drop(feature, axis=1), pd.DataFrame(X_encoded, columns=encoded_cols)], axis=1)

    return df_encoded, encoder