"""
* Folder - pipeline
* Folder purpose - Acts as a backend layer for Streamlit pages.
* File - 01_preprocess.py
* File purpose - Handle preprocessing stage, including : 
    1. Fetch fresh dataset. (Using 'utils' function)
    2. Drop duplicates, missing rows.
    3. Create new features.
    4. Drop features not required by ML models. (Using 'utils' function)
    5. Encode categorical features and scale the dataset. (Encode using 'utils' function)

* Output - 'satellite_processed.csv' from a series of functions.
"""

# Required libraries for this component / file
import math
import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from joblib import dump


def drop_rows(df):
    """ 
    1. Drop duplicated rows. 
    2. Drop rows having missing values.

    Args:
        df (DataFrame): Raw dataframe
    
    Returns: Dataframe with clean rows
    """

    df = df.drop_duplicates()
    df = df.dropna()

    return df
#--------------------------------------------------------

def create_features(df):
    """
    1. Creates orbital features from TLE data.
    
    Adds these columns to the dataframe:
    - ORBIT_PERIOD_SEC: Time for one orbit (seconds) (Optional)
    - SEMI_MAJOR_AXIS: Average orbital radius (km)
    - ORBIT_HEIGHT: Altitude above Earth surface (km)
    - PERIGEE: Lowest point altitude (km)
    - APOGEE: Highest point altitude (km)
    - ORBITAL_SPEED: Satellite velocity (km/s)
    - AGE_SINCE_LAUNCH: Age of satellite since launch (years)
    - SATELLITE_TYPE: Describes the type of payload

    2. Filters to LEO satellites only (160-2000 km altitude).
    
    Args:
        df: DataFrame with cleaned satellite TLE data
    
    Returns:
        DataFrame with new orbital features added 
    """
    
    # Compute Earth's gravitational parameter
    G = 6.67430e-11  # Gravitational constant (G) in N m^2/kg^2
    M_earth = 5.972e24 # Mass of Earth (M_E) in kg
    mu_earth= G * M_earth  # In m^3/s^2

    # Compute Semi major axis (From Earth's center) of satellites
    df['SEMI_MAJOR_AXIS'] = ((mu_earth * df['ORBIT_PERIOD_SEC'] ** 2 ) / (4*math.pi**2)) **(1/3) / 1000

    # Compute average orbit height (From Earth's surface)
    df['ORBIT_HEIGHT'] = df['SEMI_MAJOR_AXIS'] -  6371

    # IMPORTANT! Filter for LEO satellites
    df = df[(df['ORBIT_HEIGHT'] >=160) & (df['ORBIT_HEIGHT'] <=2000)].reset_index(drop=True)

    # Compute Perigee and apogee (From Earth's surface)
    df['PERIGEE'] = df['SEMI_MAJOR_AXIS'] * (1 - df['ECCENTRICITY']) - 6378 
    df['APOGEE'] = df['SEMI_MAJOR_AXIS'] * (1 + df['ECCENTRICITY']) - 6378

    # Compute Orbital speed (km/s)
    df['ORBITAL_SPEED'] = np.sqrt(mu_earth / (df['SEMI_MAJOR_AXIS'] * 1000)) / 1000

    # Compute approximate age since launch of the satellite
    df['EPOCH'] = pd.to_datetime(df['EPOCH'])

    df['AGE_SINCE_LAUNCH'] = round(
        df['EPOCH'].dt.year + df['EPOCH'].dt.dayofyear / 365.25 - df['OBJECT_ID'].str.split('-').str[0].astype(int), 1
    )

    # Find the payload type
    df['SAT_TYPE'] = df['OBJECT_ID'].str.extract(r'([A-Z])$') # capture anything A-Z as a group

    return df
#--------------------------------------------------------


def encode_category(df, feature):
    """
    Encode categorical features using OneHotEncoder.

    Args:
        df (DataFrame): A dataframe containing categorical feature
        col (String): Feature to OneHotEncode.
    
    Returns: Dataframe with encoded feature
    """

    # Fit and transform
    encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    X_encoded = encoder.fit_transform(df[[feature]])

    # Get actual category names
    encoded_cols = encoder.get_feature_names_out([feature])

    # Convert to DataFrame with proper column names
    df_encoded = pd.concat([df.drop(feature, axis=1), pd.DataFrame(X_encoded, columns=encoded_cols)], axis=1)

    # Save the encoder for future 
    dump(encoder, '../data/models/encoder_sat_type.joblib')

    return df_encoded
#--------------------------------------------------------


def scale_dataset(df):
    """
    Scale the dataset using 'Standardization' (mean=0, SD=1)

    Args:
        df (DataFrame): Dataframe with 'scalable' column values
    
    Returns: 
        Dataframe with scaled values
    """

    encoded_cols = [col for col in df.columns if col.startswith('SAT_TYPE_')]
    # Drop the categorical cols not requiring scaling
    numeric_cols = df.drop(columns = encoded_cols).columns

    ct = ColumnTransformer([  # lets you apply different preprocessing to different columns
        ('scaler', StandardScaler(), numeric_cols), # scale numeric feature
        ('pass', 'passthrough', encoded_cols) # keep encoded columns as is
    ])

    df_scaled = ct.fit_transform(df)
    # convert to dataframe                # numeric_col is a series, so convert to a list 
    df_scaled = pd.DataFrame(df_scaled, columns = numeric_cols.tolist() + encoded_cols)

    return df_scaled