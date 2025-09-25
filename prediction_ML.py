"""
Football Match Prediction Pipeline
Predicts match results (classification) and goals (regression) using historical data.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score, f1_score, confusion_matrix, 
    mean_absolute_error, mean_squared_error
)
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

# ----------------------------
# DATA PREPROCESSING FUNCTIONS
# ----------------------------

def load_and_preprocess_data(filepath):
    """
    Load dataset from Excel file and perform initial preprocessing.
    
    Args:
        filepath (str): Path to the Excel file (.xlsx or .xls)
        
    Returns:
        pd.DataFrame: Preprocessed dataframe
    """
    df = pd.read_excel(enhanced_football_matches.xlsx)
    
    # Convert date to datetime if it's not already
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        
    # Create result column if it doesn't exist
    if 'result' not in df.columns:
        df['result'] = df.apply(
            lambda row: 'H' if row['home_goals'] > row['away_goals'] 
                       else 'A' if row['away_goals'] > row['home_goals'] 
                       else 'D', axis=1
        )
    
    return df

def handle_missing_values(df):
    """
    Handle missing values in the dataset.
    
    Args:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        pd.DataFrame: Dataframe with missing values handled
    """
    # Make a copy to avoid modifying the original
    df_processed = df.copy()
    
    # Identify numerical and categorical columns
    numerical_cols = df_processed.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df_processed.select_dtypes(exclude=[np.number]).columns.tolist()
    
    # Remove target variables from numerical columns if present
    targets = ['home_goals', 'away_goals', 'result']
    numerical_cols = [col for col in numerical_cols if col not in targets]
    
    # Handle missing values in numerical columns with median
    for col in numerical_cols:
        if df_processed[col].isnull().any():
            df_processed[col].fillna(df_processed[col].median(), inplace=True)
    
    # Handle missing values in categorical columns with mode
    for col in categorical_cols:
        if col in df_processed.columns and df_processed[col].isnull().any():
            mode_value = df_processed[col].mode()
            if len(mode_value) > 0:
                df_processed[col].fillna(mode_value[0], inplace=True)
            else:
                df_processed[col].fillna('Unknown', inplace=True)
    
    return df_processed

def encode_team_features(df):
    """
    Encode home_team and away_team using Label Encoding.
    
    Args:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        pd.DataFrame: Dataframe with encoded team features
        dict: Dictionary containing label encoders for teams
    """
    df_encoded = df.copy()
    encoders = {}
    
    team_columns = ['home_team', 'away_team']
    
    # Create a combined list of all teams for consistent encoding
    all_teams = pd.concat([df['home_team'], df['away_team']]).unique()
    
    # Create and fit label encoder for teams
    team_encoder = LabelEncoder()
    team_encoder.fit(all_teams)
    
    # Apply encoding to both home and away teams
    for col in team_columns:
        if col in df_encoded.columns:
            df_encoded[f'{col}_encoded'] = team_encoder.transform(df_encoded[col])
    
    encoders['team_encoder'] = team_encoder
    
    return df_encoded, encoders

def prepare_features_and_targets(df):
    """
    Prepare feature matrix and target variables.
    
    Args:
        df (pd.DataFrame): Preprocessed dataframe
        
    Returns:
        tuple: (X, y_classification, y_regression_home, y_regression_away)
    """
    # Define feature columns (excluding targets and original team names)
    feature_cols = [
        'home_last5_points', 'away_last5_points',
        'home_last5_goals_scored', 'away_last5_goals_scored',
        'home_last5_goals_conceded', 'away_last5_goals_conceded',
        'head_to_head_wins_home', 'head_to_head_wins_away',
        'home_league_position', 'away_league_position',
        'home_team_encoded', 'away_team_encoded'
    ]
    
    # Ensure all feature columns exist
    available_features = [col for col in feature_cols if col in df.columns]
    
    X = df[available_features].copy()
    y_classification = df['result'].copy()
    y_regression_home = df['home_goals'].copy()
    y_regression_away = df['away_goals'].copy()
    
    return X, y_classification, y_regression_home, y_regression_away

def scale_features(X_train, X_test):
    """
    Scale numerical features using StandardScaler.
    
    Args:
        X_train (pd.DataFrame): Training features
        X_test (pd.DataFrame): Test features
        
    Returns:
        tuple: (X_train_scaled, X_test_scaled, scaler)
    """
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Convert back to DataFrame to maintain column names
    X_train_scaled = pd.DataFrame(X_train_scaled, columns=X_train.columns, index=X_train.index)
    X_test_scaled = pd.DataFrame(X_test_scaled, columns=X_test.columns, index=X_test.index)
    
    return X_train_scaled, X_test_scaled, scaler

# ----------------------------
# MODEL TRAINING AND EVALUATION
# ----------------------------

def train_classification_model(X_train, X_test, y_train, y_test, model_type='random_forest'):
    """
    Train and evaluate classification model for match result prediction.
    
    Args:
        X_train, X_test: Training and test features
        y_train, y_test: Training and test targets
        model_type (str): 'random_forest' or 'xgboost'
        
    Returns:
        tuple: (trained_model, metrics_dict, predictions)
    """
    if model_type == 'random_forest':
        model = RandomForestClassifier(n_estimators=100, random_state=42)
    elif model_type == 'xgboost':
        model = xgb.XGBClassifier(n_estimators=100, random_state=42, use_label_encoder=False, eval_metric='logloss')
    else:
        raise ValueError("model_type must be 'random_forest' or 'xgboost'")
    
    # Train model
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')  # Use weighted for multi-class
    cm = confusion_matrix(y_test, y_pred)
    
    metrics = {
        'accuracy': accuracy,
        'f1_score': f1,
        'confusion_matrix': cm
    }
    
    return model, metrics, y_pred

def train_regression_models(X_train, X_test, y_train_home, y_train_away, y_test_home, y_test_away, model_type='random_forest'):
    """
    Train and evaluate regression models for home and away goals prediction.
    
    Args:
        X_train, X_test: Training and test features
        y_train_home, y_train_away: Training targets for home and away goals
        y_test_home, y_test_away: Test targets for home and away goals
        model_type (str): 'random_forest' or 'xgboost'
        
    Returns:
        tuple: (home_model, away_model, metrics_dict, home_pred, away_pred)
    """
    if model_type == 'random_forest':
        home_model = RandomForestRegressor(n_estimators=100, random_state=42)
        away_model = RandomForestRegressor(n_estimators=100, random_state=42)
    elif model_type == 'xgboost':
        home_model = xgb.XGBRegressor(n_estimators=100, random_state=42)
        away_model = xgb.XGBRegressor(n_estimators=100, random_state=42)
    else:
        raise ValueError("model_type must be 'random_forest' or 'xgboost'")
    
    # Train models
    home_model.fit(X_train, y_train_home)
    away_model.fit(X_train, y_train_away)
    
    # Make predictions
    home_pred = home_model.predict(X_test)
    away_pred = away_model.predict(X_test)
    
    # Calculate metrics for home goals
    mae_home = mean_absolute_error(y_test_home, home_pred)
    rmse_home = np.sqrt(mean_squared_error(y_test_home, home_pred))
    
    # Calculate metrics for away goals
    mae_away = mean_absolute_error(y_test_away, away_pred)
    rmse_away = np.sqrt(mean_squared_error(y_test_away, away_pred))
    
    metrics = {
        'home_goals': {'mae': mae_home, 'rmse': rmse_home},
        'away_goals': {'mae': mae_away, 'rmse': rmse_away}
    }
    
    return home_model, away_model, metrics, home_pred, away_pred

def print_evaluation_results(class_metrics, reg_metrics, model_type):
    """
    Print evaluation results in a clear format.
    
    Args:
        class_metrics (dict): Classification metrics
        reg_metrics (dict): Regression metrics
        model_type (str): Type of model used
    """
    print(f"\n{'='*60}")
    print(f"EVALUATION RESULTS - {model_type.upper()}")
    print(f"{'='*60}")
    
    # Classification results
    print(f"\n📊 CLASSIFICATION (Match Result Prediction):")
    print(f"   Accuracy: {class_metrics['accuracy']:.4f}")
    print(f"   F1-Score: {class_metrics['f1_score']:.4f}")
    print(f"\n   Confusion Matrix:")
    print(f"   {class_metrics['confusion_matrix']}")
    
    # Regression results
    print(f"\n📈 REGRESSION (Goals Prediction):")
    print(f"   Home Goals - MAE: {reg_metrics['home_goals']['mae']:.4f}, RMSE: {reg_metrics['home_goals']['rmse']:.4f}")
    print(f"   Away Goals - MAE: {reg_metrics['away_goals']['mae']:.4f}, RMSE: {reg_metrics['away_goals']['rmse']:.4f}")

def show_example_predictions(df_test, y_class_pred, home_goals_pred, away_goals_pred, num_examples=5):
    """
    Show example predictions for test samples.
    
    Args:
        df_test (pd.DataFrame): Test dataframe
        y_class_pred (array): Predicted match results
        home_goals_pred (array): Predicted home goals
        away_goals_pred (array): Predicted away goals
        num_examples (int): Number of examples to show
    """
    print(f"\n{'='*80}")
    print(f"EXAMPLE PREDICTIONS (First {num_examples} test samples)")
    print(f"{'='*80}")
    
    # Round predicted goals to nearest integer for display
    home_goals_pred_rounded = np.round(home_goals_pred).astype(int)
    away_goals_pred_rounded = np.round(away_goals_pred).astype(int)
    
    for i in range(min(num_examples, len(df_test))):
        actual_result = df_test.iloc[i]['result']
        actual_home_goals = df_test.iloc[i]['home_goals']
        actual_away_goals = df_test.iloc[i]['away_goals']
        
        print(f"\nMatch {i+1}: {df_test.iloc[i]['home_team']} vs {df_test.iloc[i]['away_team']}")
        print(f"   Actual: {actual_home_goals}-{actual_away_goals} ({actual_result})")
        print(f"   Predicted: {home_goals_pred_rounded[i]}-{away_goals_pred_rounded[i]} ({y_class_pred[i]})")

# ----------------------------
# MAIN EXECUTION FUNCTION
# ----------------------------

def main(filepath, model_type='random_forest', test_size=0.2):
    """
    Main function to run the complete pipeline.
    
    Args:
        filepath (str): Path to Excel file
        model_type (str): 'random_forest' or 'xgboost'
        test_size (float): Proportion of dataset to include in test split
    """
    print("🚀 Starting Football Match Prediction Pipeline...")
    
    # Load and preprocess data
    print("1. Loading and preprocessing data...")
    df = load_and_preprocess_data(filepath)
    df = handle_missing_values(df)
    
    # Encode team features
    print("2. Encoding team features...")
    df_encoded, encoders = encode_team_features(df)
    
    # Prepare features and targets
    print("3. Preparing features and targets...")
    X, y_class, y_home, y_away = prepare_features_and_targets(df_encoded)
    
    # Split data
    print("4. Splitting data into train/test sets...")
    X_train, X_test, y_class_train, y_class_test = train_test_split(
        X, y_class, test_size=test_size, random_state=42, stratify=y_class
    )
    
    X_train_reg, X_test_reg, y_home_train, y_home_test = train_test_split(
        X, y_home, test_size=test_size, random_state=42
    )
    
    _, _, y_away_train, y_away_test = train_test_split(
        X, y_away, test_size=test_size, random_state=42
    )
    
    # Scale features
    print("5. Scaling features...")
    X_train_scaled, X_test_scaled, scaler = scale_features(X_train, X_test)
    
    # Train classification model
    print("6. Training classification model...")
    class_model, class_metrics, y_class_pred = train_classification_model(
        X_train_scaled, X_test_scaled, y_class_train, y_class_test, model_type
    )
    
    # Train regression models
    print("7. Training regression models...")
    home_model, away_model, reg_metrics, home_pred, away_pred = train_regression_models(
        X_train_scaled, X_test_scaled, y_home_train, y_away_train, y_home_test, y_away_test, model_type
    )
    
    # Print results
    print_evaluation_results(class_metrics, reg_metrics, model_type)
    
    # Show example predictions
    df_test_sample = df.iloc[X_test.index].copy()
    show_example_predictions(df_test_sample, y_class_pred, home_pred, away_pred)
    
    print(f"\n✅ Pipeline completed successfully!")
    
    # Return models and results for further use
    return {
        'classification_model': class_model,
        'home_goals_model': home_model,
        'away_goals_model': away_model,
        'scaler': scaler,
        'encoders': encoders,
        'metrics': {'classification': class_metrics, 'regression': reg_metrics}
    }

# ----------------------------
# USAGE EXAMPLE
# ----------------------------

if __name__ == "__main__":
    # Replace 'your_football_data.xlsx' with your actual file path
    FILEPATH = "your_football_data.xlsx"
    
    # Run with Random Forest
    print("Running with Random Forest...")
    results_rf = main(FILEPATH, model_type='random_forest')
    
    # Uncomment to run with XGBoost
    # print("\n" + "="*80)
    # print("Running with XGBoost...")
    # results_xgb = main(FILEPATH, model_type='xgboost')