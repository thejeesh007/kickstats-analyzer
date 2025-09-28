import joblib
import numpy as np
import os

def load_saved_models():
    """
    Load the trained classification model and encoders
    
    Returns:
        tuple: (classification_model, home_encoder, away_encoder, result_encoder) or (None, None, None, None) if error
    """
    models_dir = "football_models"
    
    try:
        print("🔄 Loading saved models and encoders...")
        
        # Load classification model
        class_model = joblib.load(os.path.join(models_dir, 'classification_model.pkl'))
        
        # Load encoders
        home_encoder = joblib.load(os.path.join(models_dir, 'home_team_encoder.pkl'))
        away_encoder = joblib.load(os.path.join(models_dir, 'away_team_encoder.pkl'))
        result_encoder = joblib.load(os.path.join(models_dir, 'result_encoder.pkl'))
        
        print("✅ Models and encoders loaded successfully!")
        
        # Display available teams
        print(f"\n📋 Available Teams ({len(home_encoder.classes_)} teams):")
        teams = sorted(home_encoder.classes_)
        for i, team in enumerate(teams, 1):
            print(f"{i:2d}. {team}")
        
        return class_model, home_encoder, away_encoder, result_encoder
        
    except FileNotFoundError as e:
        print(f"❌ Error: Model files not found!")
        print(f"Make sure you have trained and saved the models first.")
        print(f"Expected directory: {models_dir}")
        print(f"Missing file: {str(e)}")
        return None, None, None, None
    
    except Exception as e:
        print(f"❌ Error loading models: {str(e)}")
        return None, None, None, None

def get_team_input(prompt, encoder, team_type):
    """
    Get team input from user with validation
    
    Args:
        prompt: Input prompt message
        encoder: LabelEncoder for the teams
        team_type: "Home" or "Away" for error messages
    
    Returns:
        str: Valid team name or None if cancelled
    """
    available_teams = list(encoder.classes_)
    
    while True:
        team_input = input(prompt).strip()
        
        # Allow user to quit
        if team_input.lower() in ['quit', 'exit', 'q']:
            return None
        
        # Check if team exists (case-insensitive)
        team_matches = [team for team in available_teams if team.lower() == team_input.lower()]
        
        if team_matches:
            return team_matches[0]  # Return the correctly cased team name
        
        # If not found, show suggestions
        print(f"❌ '{team_input}' not found in available teams.")
        
        # Find similar team names
        suggestions = [team for team in available_teams if team_input.lower() in team.lower()]
        
        if suggestions:
            print(f"💡 Did you mean one of these?")
            for suggestion in suggestions[:5]:  # Show max 5 suggestions
                print(f"   - {suggestion}")
        else:
            print(f"💡 Available teams include: {', '.join(available_teams[:5])}...")
        
        print(f"   Type 'quit' to exit")
        print()

def create_feature_vector(home_encoded, away_encoded):
    """
    Create feature vector for prediction (using average values for missing features)
    
    Args:
        home_encoded: Encoded home team
        away_encoded: Encoded away team
    
    Returns:
        np.array: Feature vector for prediction
    """
    # For the advanced model, we need 15 features
    # Since we only have team names, we'll use reasonable default values for other features
    features = [
        home_encoded,      # home_team_encoded
        away_encoded,      # away_team_encoded
        1.5,              # home_recent_form (average)
        1.3,              # away_recent_form (average)
        1.7,              # home_avg_goals_for (average home goals)
        1.1,              # home_avg_goals_against
        1.3,              # away_avg_goals_for (average away goals)
        1.5,              # away_avg_goals_against
        0.5,              # home_win_rate (50%)
        0.35,             # away_win_rate (35% - away disadvantage)
        1.0,              # home_strength (average)
        0.8,              # away_strength (slightly lower for away)
        0.6,              # goal_difference_home
        -0.2,             # goal_difference_away
        0.5,              # h2h_home_advantage (neutral)
        10,               # matches_played_home
        10                # matches_played_away
    ]
    
    return np.array([features])

def predict_match_result(class_model, home_encoder, away_encoder, result_encoder, home_team, away_team):
    """
    Predict the match result for given teams
    
    Args:
        class_model: Trained classification model
        home_encoder, away_encoder, result_encoder: Encoders
        home_team, away_team: Team names
    
    Returns:
        tuple: (predicted_result, confidence, probabilities)
    """
    try:
        # Encode team names
        home_encoded = home_encoder.transform([home_team])[0]
        away_encoded = away_encoder.transform([away_team])[0]
        
        # Create feature vector
        X_predict = create_feature_vector(home_encoded, away_encoded)
        
        # Make prediction
        prediction_encoded = class_model.predict(X_predict)[0]
        prediction_proba = class_model.predict_proba(X_predict)[0]
        
        # Decode result
        predicted_result = result_encoder.inverse_transform([prediction_encoded])[0]
        confidence = np.max(prediction_proba)
        
        # Get probabilities for each outcome
        prob_dict = {}
        for i, result_class in enumerate(result_encoder.classes_):
            prob_dict[result_class] = prediction_proba[i]
        
        return predicted_result, confidence, prob_dict
        
    except Exception as e:
        print(f"❌ Error making prediction: {str(e)}")
        return None, None, None

def format_prediction_output(predicted_result, home_team, away_team, confidence, probabilities):
    """
    Format and print the prediction result in user-friendly format
    
    Args:
        predicted_result: 'H', 'A', or 'D'
        home_team, away_team: Team names
        confidence: Prediction confidence
        probabilities: Dictionary of outcome probabilities
    """
    print("\n" + "="*50)
    print("🔮 MATCH PREDICTION RESULT")
    print("="*50)
    
    print(f"🏠 Home Team: {home_team}")
    print(f"✈️  Away Team: {away_team}")
    print()
    
    # Main prediction
    if predicted_result == 'H':
        print(f"🏆 Predicted Winner: Home Team ({home_team})")
    elif predicted_result == 'A':
        print(f"🏆 Predicted Winner: Away Team ({away_team})")
    elif predicted_result == 'D':
        print(f"🤝 Predicted Result: Draw")
    
    print(f"📊 Confidence: {confidence:.1%}")
    
    # Show all probabilities
    print(f"\n📈 Outcome Probabilities:")
    print(f"   🏠 Home Win ({home_team}): {probabilities.get('H', 0):.1%}")
    print(f"   🤝 Draw: {probabilities.get('D', 0):.1%}")
    print(f"   ✈️  Away Win ({away_team}): {probabilities.get('A', 0):.1%}")
    
    print("="*50)

def main():
    """
    Main interactive prediction function
    """
    print("⚽ FOOTBALL MATCH RESULT PREDICTOR")
    print("="*50)
    print("This tool predicts the outcome of football matches using your trained model.")
    print()
    
    # Load models
    class_model, home_encoder, away_encoder, result_encoder = load_saved_models()
    
    if class_model is None:
        print("❌ Cannot proceed without trained models. Please train the model first.")
        return
    
    print("\n🎯 Ready for predictions!")
    print("Type 'quit' at any time to exit.")
    print()
    
    # Interactive prediction loop
    while True:
        print("-" * 50)
        
        # Get home team
        home_team = get_team_input("🏠 Enter Home Team: ", home_encoder, "Home")
        if home_team is None:
            break
        
        # Get away team
        away_team = get_team_input("✈️  Enter Away Team: ", away_encoder, "Away")
        if away_team is None:
            break
        
        # Check for same team
        if home_team.lower() == away_team.lower():
            print("❌ Home and away teams cannot be the same!")
            continue
        
        # Make prediction
        print(f"\n🤔 Analyzing: {home_team} vs {away_team}...")
        
        predicted_result, confidence, probabilities = predict_match_result(
            class_model, home_encoder, away_encoder, result_encoder, 
            home_team, away_team
        )
        
        if predicted_result is not None:
            format_prediction_output(predicted_result, home_team, away_team, confidence, probabilities)
        
        # Ask for another prediction
        print(f"\n🔄 Would you like to make another prediction?")
        continue_choice = input("Enter 'y' for yes, anything else to quit: ").strip().lower()
        
        if continue_choice not in ['y', 'yes']:
            break
        
        print()
    
    print("\n👋 Thanks for using the Football Match Predictor!")
    print("⚽ Good luck with your predictions!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Prediction session interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        print("Please check your model files and try again.")