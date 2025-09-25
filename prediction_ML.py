"""
Football Match Prediction Pipeline - Customized for Your Dataset
Predicts match winner and goals scored using your actual match data.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import (
    accuracy_score, f1_score, confusion_matrix, 
    mean_absolute_error, mean_squared_error, r2_score,
    classification_report
)
import warnings
warnings.filterwarnings('ignore')

# Try to import XGBoost, use RandomForest as fallback
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("XGBoost not available. Using RandomForest.")

class FootballPredictor:
    def __init__(self):
        self.classification_model = None
        self.home_goals_model = None
        self.away_goals_model = None
        self.scaler = None
        self.team_encoder = None
        self.result_encoder = None
        self.feature_columns = []
        
    def load_and_preprocess_data(self, filepath):
        """Load and preprocess the dataset"""
        print(f"Loading data from: {filepath}")
        
        try:
            df = pd.read_excel(filepath)
            print(f"Successfully loaded {len(df)} rows and {len(df.columns)} columns")
            print(f"Columns: {list(df.columns)}")
            
        except FileNotFoundError:
            print(f"Error: File '{filepath}' not found!")
            raise
        except Exception as e:
            print(f"Error loading file: {e}")
            raise
        
        return df
    
    def extract_goals_and_results(self, df):
        """Extract goals and match results from your dataset"""
        df_processed = df.copy()
        
        print("Extracting goals and results from your dataset...")
        
        # Your dataset has 'final_scor' column - let's extract from there
        if 'final_scor' in df.columns:
            print("Found 'final_scor' column, extracting goals...")
            
            def parse_score(score_str):
                if pd.isna(score_str) or str(score_str).strip() == '':
                    return pd.Series([np.nan, np.nan])
                
                try:
                    score_str = str(score_str).strip()
                    if '-' in score_str:
                        parts = score_str.split('-')
                        if len(parts) == 2:
                            home_goals = int(float(parts[0].strip()))
                            away_goals = int(float(parts[1].strip()))
                            return pd.Series([home_goals, away_goals])
                except:
                    pass
                
                return pd.Series([np.nan, np.nan])
            
            # Extract goals
            df_processed[['home_goals', 'away_goals']] = df_processed['final_scor'].apply(parse_score)
            
            # Count extracted matches
            completed_matches = df_processed[['home_goals', 'away_goals']].dropna().shape[0]
            print(f"Extracted goals from {completed_matches} completed matches")
            
            # Create match result
            def determine_result(row):
                if pd.isna(row['home_goals']) or pd.isna(row['away_goals']):
                    return None
                elif row['home_goals'] > row['away_goals']:
                    return 'H'  # Home win
                elif row['away_goals'] > row['home_goals']:
                    return 'A'  # Away win
                else:
                    return 'D'  # Draw
            
            df_processed['result'] = df_processed.apply(determine_result, axis=1)
            
            if df_processed['result'].notna().sum() > 0:
                result_counts = df_processed['result'].value_counts()
                print(f"Match results: {dict(result_counts)}")
        
        # Filter only completed matches for training
        completed_mask = df_processed['match_status'] == 'completed'
        completed_df = df_processed[completed_mask].copy()
        print(f"Found {len(completed_df)} completed matches for training")
        
        return completed_df
    
    def prepare_features(self, df):
        """Prepare feature matrix using your dataset columns"""
        df_processed = df.copy()
        
        # Your actual column names from the dataset
        self.feature_columns = [
            'home_points_last5',
            'away_points_last5', 
            'home_goals_scored_last5',
            'away_goals_scored_last5',
            'home_goals_conceded_last5',
            'away_goals_conceded_last5',
            'home_league_position',
            'away_league_position',
            'goal_difference_home',
            'goal_difference_away',
            'home_team_encoded',
            'away_team_encoded'
        ]
        
        # Fill missing numerical values with median
        numerical_cols = [
            'home_points_last5', 'away_points_last5',
            'home_goals_scored_last5', 'away_goals_scored_last5', 
            'home_goals_conceded_last5', 'away_goals_conceded_last5',
            'home_league_position', 'away_league_position',
            'goal_difference_home', 'goal_difference_away'
        ]
        
        for col in numerical_cols:
            if col in df_processed.columns:
                df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce')
                median_val = df_processed[col].median()
                df_processed[col] = df_processed[col].fillna(median_val)
        
        # Encode teams
        if 'home_team' in df_processed.columns and 'away_team' in df_processed.columns:
            # Get all unique teams
            all_teams = pd.concat([df_processed['home_team'], df_processed['away_team']]).unique()
            all_teams = [str(team) for team in all_teams if str(team) != 'nan']
            
            if self.team_encoder is None:
                self.team_encoder = LabelEncoder()
                self.team_encoder.fit(all_teams)
            
            # Encode team names
            df_processed['home_team_encoded'] = self.team_encoder.transform(df_processed['home_team'].astype(str))
            df_processed['away_team_encoded'] = self.team_encoder.transform(df_processed['away_team'].astype(str))
        
        # Select available features
        available_features = [col for col in self.feature_columns if col in df_processed.columns]
        print(f"Using {len(available_features)} features: {available_features}")
        
        return df_processed[available_features]
    
    def train_models(self, filepath_or_df, model_type='random_forest'):
        """Train prediction models using your data"""
        print("\n=== Training Football Match Prediction Models ===")
        
        # Load data if filepath is provided
        if isinstance(filepath_or_df, str):
            df = self.load_and_preprocess_data(filepath_or_df)
        else:
            df = filepath_or_df
        
        # Extract goals and results from completed matches
        df_processed = self.extract_goals_and_results(df)
        
        if len(df_processed) == 0:
            print("No completed matches found for training!")
            return
        
        # Prepare features
        print("\nPreparing features...")
        X = self.prepare_features(df_processed)
        
        # Prepare targets
        y_result = df_processed['result'] if 'result' in df_processed.columns else None
        y_home_goals = df_processed['home_goals'] if 'home_goals' in df_processed.columns else None
        y_away_goals = df_processed['away_goals'] if 'away_goals' in df_processed.columns else None
        
        print(f"Training data shape: {X.shape}")
        print(f"Valid results: {y_result.notna().sum() if y_result is not None else 0}")
        print(f"Valid goals: {y_home_goals.notna().sum() if y_home_goals is not None else 0}")
        
        # Train classification model (match winner prediction)
        if y_result is not None and y_result.notna().sum() > 5:
            print(f"\n--- Training Match Winner Prediction Model ---")
            
            # Remove rows with missing targets
            mask = y_result.notna() & X.notna().all(axis=1)
            X_class = X[mask]
            y_class = y_result[mask]
            
            print(f"Training samples: {len(X_class)}")
            print(f"Result distribution: {y_class.value_counts().to_dict()}")
            
            if len(y_class.unique()) > 1:  # Need at least 2 classes
                # Encode results
                self.result_encoder = LabelEncoder()
                y_class_encoded = self.result_encoder.fit_transform(y_class)
                
                # Split data
                X_train, X_test, y_train, y_test = train_test_split(
                    X_class, y_class_encoded, test_size=0.2, random_state=42, 
                    stratify=y_class_encoded
                )
                
                # Scale features
                self.scaler = StandardScaler()
                X_train_scaled = self.scaler.fit_transform(X_train)
                X_test_scaled = self.scaler.transform(X_test)
                
                # Choose model
                if model_type == 'xgboost' and XGBOOST_AVAILABLE:
                    self.classification_model = xgb.XGBClassifier(
                        n_estimators=100, random_state=42, eval_metric='logloss'
                    )
                else:
                    self.classification_model = RandomForestClassifier(
                        n_estimators=100, random_state=42, class_weight='balanced'
                    )
                
                # Train model
                self.classification_model.fit(X_train_scaled, y_train)
                
                # Evaluate
                y_pred = self.classification_model.predict(X_test_scaled)
                accuracy = accuracy_score(y_test, y_pred)
                f1 = f1_score(y_test, y_pred, average='weighted')
                
                print(f"✓ Match winner prediction accuracy: {accuracy:.3f}")
                print(f"✓ F1-Score: {f1:.3f}")
                print(f"✓ Result classes: {list(self.result_encoder.classes_)}")
            else:
                print("Only one class found in results, skipping classification model")
        
        # Train goal prediction models
        if y_home_goals is not None and y_away_goals is not None:
            print(f"\n--- Training Goal Prediction Models ---")
            
            # Remove rows with missing targets
            mask = (y_home_goals.notna() & y_away_goals.notna() & X.notna().all(axis=1))
            X_reg = X[mask]
            y_home = y_home_goals[mask]
            y_away = y_away_goals[mask]
            
            print(f"Training samples: {len(X_reg)}")
            print(f"Average goals - Home: {y_home.mean():.2f}, Away: {y_away.mean():.2f}")
            
            if len(X_reg) > 5:
                # Split data
                X_train, X_test, y_home_train, y_home_test = train_test_split(
                    X_reg, y_home, test_size=0.2, random_state=42
                )
                _, _, y_away_train, y_away_test = train_test_split(
                    X_reg, y_away, test_size=0.2, random_state=42
                )
                
                # Use same scaler as classification or create new one
                if self.scaler is None:
                    self.scaler = StandardScaler()
                    X_train_scaled = self.scaler.fit_transform(X_train)
                else:
                    X_train_scaled = self.scaler.transform(X_train)
                
                X_test_scaled = self.scaler.transform(X_test)
                
                # Choose models
                if model_type == 'xgboost' and XGBOOST_AVAILABLE:
                    self.home_goals_model = xgb.XGBRegressor(n_estimators=100, random_state=42)
                    self.away_goals_model = xgb.XGBRegressor(n_estimators=100, random_state=42)
                else:
                    self.home_goals_model = RandomForestRegressor(n_estimators=100, random_state=42)
                    self.away_goals_model = RandomForestRegressor(n_estimators=100, random_state=42)
                
                # Train models
                self.home_goals_model.fit(X_train_scaled, y_home_train)
                self.away_goals_model.fit(X_train_scaled, y_away_train)
                
                # Evaluate
                home_pred = self.home_goals_model.predict(X_test_scaled)
                away_pred = self.away_goals_model.predict(X_test_scaled)
                
                home_mae = mean_absolute_error(y_home_test, home_pred)
                away_mae = mean_absolute_error(y_away_test, away_pred)
                home_r2 = r2_score(y_home_test, home_pred)
                away_r2 = r2_score(y_away_test, away_pred)
                
                print(f"✓ Home goals MAE: {home_mae:.3f}, R²: {home_r2:.3f}")
                print(f"✓ Away goals MAE: {away_mae:.3f}, R²: {away_r2:.3f}")
        
        print("\n=== Model Training Completed Successfully! ===")
    
    def predict_match(self, home_team, away_team, home_stats=None, away_stats=None):
        """Predict match outcome and score"""
        
        if self.classification_model is None and self.home_goals_model is None:
            return {"error": "No trained models available. Please train models first."}
        
        # Default stats if not provided
        if home_stats is None:
            home_stats = {
                'points_last5': 8,
                'goals_scored_last5': 7,
                'goals_conceded_last5': 5,
                'league_position': 10,
                'goal_difference': 2
            }
        
        if away_stats is None:
            away_stats = {
                'points_last5': 7,
                'goals_scored_last5': 6,
                'goals_conceded_last5': 6,
                'league_position': 12,
                'goal_difference': 0
            }
        
        # Create prediction DataFrame
        pred_data = {
            'home_team': [str(home_team)],
            'away_team': [str(away_team)],
            'home_points_last5': [home_stats['points_last5']],
            'away_points_last5': [away_stats['points_last5']],
            'home_goals_scored_last5': [home_stats['goals_scored_last5']],
            'away_goals_scored_last5': [away_stats['goals_scored_last5']],
            'home_goals_conceded_last5': [home_stats['goals_conceded_last5']],
            'away_goals_conceded_last5': [away_stats['goals_conceded_last5']],
            'home_league_position': [home_stats['league_position']],
            'away_league_position': [away_stats['league_position']],
            'goal_difference_home': [home_stats['goal_difference']],
            'goal_difference_away': [away_stats['goal_difference']]
        }
        
        pred_df = pd.DataFrame(pred_data)
        
        # Prepare features
        X_pred = self.prepare_features(pred_df)
        
        # Scale features
        if self.scaler is not None:
            X_pred_scaled = self.scaler.transform(X_pred)
        else:
            X_pred_scaled = X_pred.values
        
        prediction_result = {}
        
        # Predict match winner
        if self.classification_model is not None and self.result_encoder is not None:
            try:
                result_proba = self.classification_model.predict_proba(X_pred_scaled)[0]
                result_pred = self.classification_model.predict(X_pred_scaled)[0]
                
                result_label = self.result_encoder.inverse_transform([result_pred])[0]
                
                # Get probabilities
                classes = self.result_encoder.classes_
                probabilities = {classes[i]: result_proba[i] for i in range(len(classes))}
                
                prediction_result['winner'] = result_label
                prediction_result['probabilities'] = probabilities
            except Exception as e:
                print(f"Error in winner prediction: {e}")
        
        # Predict goals
        if self.home_goals_model is not None and self.away_goals_model is not None:
            try:
                home_goals_pred = self.home_goals_model.predict(X_pred_scaled)[0]
                away_goals_pred = self.away_goals_model.predict(X_pred_scaled)[0]
                
                prediction_result['home_goals'] = max(0, round(home_goals_pred))
                prediction_result['away_goals'] = max(0, round(away_goals_pred))
                prediction_result['predicted_score'] = f"{prediction_result['home_goals']}-{prediction_result['away_goals']}"
            except Exception as e:
                print(f"Error in goal prediction: {e}")
        
        return prediction_result
    
    def print_prediction(self, home_team, away_team, prediction):
        """Print prediction in a formatted way"""
        print(f"\n{'='*70}")
        print(f"🏆 MATCH PREDICTION: {home_team} vs {away_team}")
        print(f"{'='*70}")
        
        if 'error' in prediction:
            print(f"❌ {prediction['error']}")
            return
        
        if 'predicted_score' in prediction:
            print(f"⚽ Predicted Score: {prediction['predicted_score']}")
        
        if 'winner' in prediction:
            winner_symbols = {'H': '🏠', 'A': '✈️', 'D': '🤝'}
            winner_text = {
                'H': f"{home_team} Win",
                'A': f"{away_team} Win", 
                'D': "Draw"
            }
            symbol = winner_symbols.get(prediction['winner'], '❓')
            print(f"{symbol} Predicted Winner: {winner_text.get(prediction['winner'], 'Unknown')}")
        
        if 'probabilities' in prediction:
            print(f"\n📊 Win Probabilities:")
            for outcome, prob in prediction['probabilities'].items():
                outcome_text = {
                    'H': f"  🏠 {home_team} Win",
                    'A': f"  ✈️  {away_team} Win",
                    'D': "  🤝 Draw"
                }
                print(f"{outcome_text.get(outcome, outcome)}: {prob:.1%}")

# Main execution function
def main():
    print("🚀 Starting Football Match Predictor")
    print("="*50)
    
    # Initialize predictor
    predictor = FootballPredictor()
    
    try:
        # Train models with your data
        predictor.train_models("enhanced_football_matches.xlsx", model_type='random_forest')
        
        print(f"\n{'='*70}")
        print("📈 MAKING SAMPLE PREDICTIONS")
        print(f"{'='*70}")
        
        # Test predictions with teams from your dataset
        test_matches = [
            ("Arsenal", "Chelsea"),
            ("Manchester City", "Liverpool"), 
            ("Tottenham", "Everton")
        ]
        
        for home, away in test_matches:
            # Example with custom stats
            home_stats = {
                'points_last5': 12,
                'goals_scored_last5': 10,
                'goals_conceded_last5': 3,
                'league_position': 3,
                'goal_difference': 7
            }
            
            away_stats = {
                'points_last5': 9,
                'goals_scored_last5': 7,
                'goals_conceded_last5': 5,
                'league_position': 8,
                'goal_difference': 2
            }
            
            prediction = predictor.predict_match(home, away, home_stats, away_stats)
            predictor.print_prediction(home, away, prediction)
        
        print(f"\n{'='*70}")
        print("✅ PREDICTION SYSTEM READY!")
        print("You can now predict any match using predictor.predict_match()")
        print(f"{'='*70}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()