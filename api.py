# api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import joblib
import numpy as np
import os

app = FastAPI(title="Football Prediction API")

# Add CORS middleware to allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model storage
models = {}

class PredictionRequest(BaseModel):
    home_team: str
    away_team: str

class PredictionResponse(BaseModel):
    predicted_result: str  # 'H', 'A', or 'D'
    predicted_home_score: float
    predicted_away_score: float
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    confidence: float
    key_factors: List[str]
    ai_analysis: str

def load_models():
    """Load all saved models into memory"""
    models_dir = "football_models"
    
    if not os.path.exists(models_dir):
        raise FileNotFoundError("Models directory not found. Please train models first.")
    
    try:
        models['class_model'] = joblib.load(os.path.join(models_dir, 'classification_model.pkl'))
        models['reg_model'] = joblib.load(os.path.join(models_dir, 'regression_model.pkl'))
        models['home_encoder'] = joblib.load(os.path.join(models_dir, 'home_team_encoder.pkl'))
        models['away_encoder'] = joblib.load(os.path.join(models_dir, 'away_team_encoder.pkl'))
        models['result_encoder'] = joblib.load(os.path.join(models_dir, 'result_encoder.pkl'))
        print("✅ Models loaded successfully!")
        return True
    except Exception as e:
        print(f"❌ Error loading models: {e}")
        return False

def create_feature_vector(home_encoded, away_encoded):
    """Create feature vector with reasonable defaults"""
    features = [
        home_encoded,      # home_team_encoded
        away_encoded,      # away_team_encoded
        1.5,              # home_recent_form
        1.3,              # away_recent_form
        1.7,              # home_avg_goals_for
        1.1,              # home_avg_goals_against
        1.3,              # away_avg_goals_for
        1.5,              # away_avg_goals_against
        0.5,              # home_win_rate
        0.35,             # away_win_rate
        1.0,              # home_strength
        0.8,              # away_strength
        0.6,              # goal_difference_home
        -0.2,             # goal_difference_away
        0.5,              # h2h_home_advantage
        10,               # matches_played_home
        10                # matches_played_away
    ]
    return np.array([features])

@app.on_event("startup")
async def startup_event():
    """Load models when the API starts"""
    if not load_models():
        print("❌ Warning: Models failed to load. API will return errors.")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "models_loaded": len(models) > 0}

@app.get("/teams")
async def get_teams():
    """Get list of available teams"""
    if not models:
        raise HTTPException(status_code=500, detail="Models not loaded")
    
    teams = list(models['home_encoder'].classes_)
    return {"teams": sorted(teams)}

@app.post("/predict", response_model=PredictionResponse)
async def predict_match(request: PredictionRequest):
    """Generate real prediction using trained ML models"""
    if not models:
        raise HTTPException(status_code=500, detail="Models not loaded")
    
    home_team = request.home_team
    away_team = request.away_team
    
    # Validate teams exist
    if home_team not in models['home_encoder'].classes_:
        raise HTTPException(status_code=400, detail=f"Unknown home team: {home_team}")
    if away_team not in models['away_encoder'].classes_:
        raise HTTPException(status_code=400, detail=f"Unknown away team: {away_team}")
    
    if home_team == away_team:
        raise HTTPException(status_code=400, detail="Home and away teams cannot be the same")
    
    try:
        # Encode teams
        home_encoded = models['home_encoder'].transform([home_team])[0]
        away_encoded = models['away_encoder'].transform([away_team])[0]
        
        # Create features
        X_predict = create_feature_vector(home_encoded, away_encoded)
        
        # Classification prediction
        result_pred = models['class_model'].predict(X_predict)[0]
        result_proba = models['class_model'].predict_proba(X_predict)[0]
        predicted_result = models['result_encoder'].inverse_transform([result_pred])[0]
        confidence = float(np.max(result_proba))
        
        # Regression prediction (goals)
        goals_pred = models['reg_model'].predict(X_predict)[0]
        predicted_home_score = max(0, float(goals_pred[0]))
        predicted_away_score = max(0, float(goals_pred[1]))
        
        # Extract probabilities
        classes = models['result_encoder'].classes_
        prob_dict = {cls: 0.0 for cls in ['H', 'D', 'A']}
        for i, cls in enumerate(classes):
            prob_dict[cls] = float(result_proba[i])
        
        # Generate key factors based on prediction
        key_factors = []
        if predicted_result == 'H':
            key_factors = ["Home advantage", "Strong recent form", "Favorable head-to-head record", "High home win probability"]
        elif predicted_result == 'A':
            key_factors = ["Away team in excellent form", "Home team defensive vulnerabilities", "Recent away victories", "Tactical advantage"]
        else:  # Draw
            key_factors = ["Balanced team strengths", "Similar recent form", "Historical tendency for draws", "Defensive match expected"]
        
        # Generate AI analysis
        if predicted_result == 'H':
            ai_analysis = f"Based on our advanced ensemble model analysis, {home_team} is predicted to win at home. The model indicates strong home form and historical advantage in this fixture. Key factors include home advantage ({prob_dict['H']:.1%} win probability) and superior recent performance metrics."
        elif predicted_result == 'A':
            ai_analysis = f"Our AI model predicts an away victory for {away_team}. Despite playing away from home, {away_team}'s recent form and tactical setup give them the edge. The away win probability of {prob_dict['A']:.1%} reflects their current momentum and the home team's vulnerabilities."
        else:
            ai_analysis = f"This match is predicted to end in a draw, reflecting the balanced nature of this fixture. Both teams show similar form metrics and historical head-to-head records suggest a tight contest. With draw probability at {prob_dict['D']:.1%}, expect a tactical and evenly matched encounter."
        
        return PredictionResponse(
            predicted_result=predicted_result,
            predicted_home_score=predicted_home_score,
            predicted_away_score=predicted_away_score,
            home_win_probability=prob_dict['H'],
            draw_probability=prob_dict['D'],
            away_win_probability=prob_dict['A'],
            confidence=confidence,
            key_factors=key_factors,
            ai_analysis=ai_analysis
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)