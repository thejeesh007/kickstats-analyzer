# ==================================================
#  FOOTBALL PREDICTION & DATA BACKEND (FASTAPI)
#  ✅ Optimized for Railway Deployment
# ==================================================
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import joblib
import numpy as np
import os
import requests
from dotenv import load_dotenv

# ============================
#  LOAD ENVIRONMENT VARIABLES
# ============================
# On Railway, environment variables are injected automatically
load_dotenv()

API_KEY = os.getenv("VITE_API_SPORTS_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://main.di04hsm56xj.amplifyapp.com")

if not API_KEY:
    print("⚠️ Warning: VITE_API_SPORTS_KEY not set in environment. Football data APIs may fail.")
else:
    print("✅ API Key loaded successfully")

# ============================
#  FASTAPI APP SETUP
# ============================
app = FastAPI(title="Football Prediction & Data API", version="2.0")

# CORS setup — restricted to known origins for security
origins = [
    "http://localhost:5173",
    FRONTEND_URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================
#  MODEL LOADING
# ============================
models = {}

class PredictionRequest(BaseModel):
    home_team: str
    away_team: str


class PredictionResponse(BaseModel):
    predicted_result: str
    predicted_home_score: float
    predicted_away_score: float
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    confidence: float
    key_factors: List[str]
    ai_analysis: str


def load_models():
    models_dir = "/backend/football_models/"
    if not os.path.exists(models_dir):
        raise FileNotFoundError("Models directory not found. Please train models first.")

    try:
        models["class_model"] = joblib.load(os.path.join(models_dir, "classification_model.pkl"))
        models["reg_model"] = joblib.load(os.path.join(models_dir, "regression_model.pkl"))
        models["home_encoder"] = joblib.load(os.path.join(models_dir, "home_team_encoder.pkl"))
        models["away_encoder"] = joblib.load(os.path.join(models_dir, "away_team_encoder.pkl"))
        models["result_encoder"] = joblib.load(os.path.join(models_dir, "result_encoder.pkl"))
        print("✅ Models loaded successfully!")
        return True
    except Exception as e:
        print(f"❌ Error loading models: {e}")
        return False


def create_feature_vector(home_encoded, away_encoded):
    """Generate numeric feature array for prediction"""
    features = [
        home_encoded, away_encoded, 1.5, 1.3, 1.7, 1.1, 1.3, 1.5,
        0.5, 0.35, 1.0, 0.8, 0.6, -0.2, 0.5, 10, 10
    ]
    return np.array([features])


@app.on_event("startup")
async def startup_event():
    """Load ML models when the API starts"""
    if not load_models():
        print("⚠️ Warning: Models failed to load. Predictions may not work.")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "models_loaded": len(models) > 0}

# ============================
#  ML PREDICTION ENDPOINTS
# ============================
@app.get("/teams")
async def get_teams():
    if not models:
        raise HTTPException(status_code=500, detail="Models not loaded")
    teams = list(models["home_encoder"].classes_)
    return {"teams": sorted(teams)}


@app.post("/predict", response_model=PredictionResponse)
async def predict_match(request: PredictionRequest):
    if not models:
        raise HTTPException(status_code=500, detail="Models not loaded")

    home_team, away_team = request.home_team, request.away_team

    if home_team not in models["home_encoder"].classes_:
        raise HTTPException(status_code=400, detail=f"Unknown home team: {home_team}")
    if away_team not in models["away_encoder"].classes_:
        raise HTTPException(status_code=400, detail=f"Unknown away team: {away_team}")
    if home_team == away_team:
        raise HTTPException(status_code=400, detail="Home and away teams cannot be the same")

    try:
        home_encoded = models["home_encoder"].transform([home_team])[0]
        away_encoded = models["away_encoder"].transform([away_team])[0]
        X_predict = create_feature_vector(home_encoded, away_encoded)

        result_pred = models["class_model"].predict(X_predict)[0]
        result_proba = models["class_model"].predict_proba(X_predict)[0]
        predicted_result = models["result_encoder"].inverse_transform([result_pred])[0]
        confidence = float(np.max(result_proba))

        goals_pred = models["reg_model"].predict(X_predict)[0]
        predicted_home_score = max(0, float(goals_pred[0]))
        predicted_away_score = max(0, float(goals_pred[1]))

        classes = models["result_encoder"].classes_
        prob_dict = {cls: 0.0 for cls in ["H", "D", "A"]}
        for i, cls in enumerate(classes):
            prob_dict[cls] = float(result_proba[i])

        key_factors = []
        if predicted_result == "H":
            key_factors = ["Home advantage", "Strong recent form", "Favorable head-to-head record", "High home win probability"]
        elif predicted_result == "A":
            key_factors = ["Away team in excellent form", "Home team defensive vulnerabilities", "Recent away victories", "Tactical advantage"]
        else:
            key_factors = ["Balanced team strengths", "Similar recent form", "Historical tendency for draws", "Defensive match expected"]

        if predicted_result == "H":
            ai_analysis = f"{home_team} is predicted to win with {prob_dict['H']:.1%} win probability due to strong home form and historical advantage."
        elif predicted_result == "A":
            ai_analysis = f"{away_team} likely wins with {prob_dict['A']:.1%} probability, showing tactical and momentum advantage."
        else:
            ai_analysis = f"A draw is predicted ({prob_dict['D']:.1%} probability), indicating balanced team performance."

        return PredictionResponse(
            predicted_result=predicted_result,
            predicted_home_score=predicted_home_score,
            predicted_away_score=predicted_away_score,
            home_win_probability=prob_dict["H"],
            draw_probability=prob_dict["D"],
            away_win_probability=prob_dict["A"],
            confidence=confidence,
            key_factors=key_factors,
            ai_analysis=ai_analysis
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

# ============================
#  FOOTBALL DATA ENDPOINTS
# ============================
BASE_URL = "https://v3.football.api-sports.io"

@app.get("/countries")
def get_countries():
    """Fetch all available countries."""
    headers = {"x-apisports-key": API_KEY}
    res = requests.get(f"{BASE_URL}/countries", headers=headers)
    return res.json()


@app.get("/leagues")
def get_leagues(country: str):
    """Fetch all leagues for a given country."""
    headers = {"x-apisports-key": API_KEY}
    url = f"{BASE_URL}/leagues?country={country}"
    res = requests.get(url, headers=headers)
    return res.json()


@app.get("/teams/{league_id}")
def get_teams_by_league(league_id: int, season: int = 2024):
    """Fetch all teams for a given league."""
    headers = {"x-apisports-key": API_KEY}
    url = f"{BASE_URL}/teams?league={league_id}&season={season}"
    res = requests.get(url, headers=headers)
    return res.json()


@app.get("/players")
def get_players(team: int, season: int = 2024):
    """Fetch players for a given team and season."""
    headers = {"x-apisports-key": API_KEY}
    url = f"{BASE_URL}/players?team={team}&season={season}"
    res = requests.get(url, headers=headers)
    return res.json()


@app.get("/fixtures")
def get_fixtures(
    league: int = Query(..., description="League ID"),
    season: int = Query(..., description="Season year"),
    team: Optional[int] = Query(None, description="Optional team ID"),
    status: Optional[str] = Query(None, description="Match status: live, finished, etc."),
):
    """Fetch fixtures (matches) for a given league and season."""
    headers = {"x-apisports-key": API_KEY}
    params = {"league": league, "season": season}

    if team:
        params["team"] = team
    if status:
        params["status"] = status

    res = requests.get(f"{BASE_URL}/fixtures", headers=headers, params=params)

    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail="Failed to fetch fixtures")

    data = res.json()
    simplified = []

    for item in data.get("response", []):
        fixture = item["fixture"]
        teams = item["teams"]
        goals = item["goals"]
        league_info = item["league"]

        simplified.append({
            "fixture_id": fixture["id"],
            "date": fixture["date"],
            "status": fixture["status"]["short"],
            "home_team": teams["home"]["name"],
            "away_team": teams["away"]["name"],
            "home_logo": teams["home"]["logo"],
            "away_logo": teams["away"]["logo"],
            "home_goals": goals["home"],
            "away_goals": goals["away"],
            "venue": fixture["venue"]["name"] if fixture.get("venue") else None,
            "league": league_info["name"],
            "season": league_info["season"]
        })

    return {"fixtures": simplified, "count": len(simplified)}

# ============================
#  RUN LOCALLY / ENTRYPOINT
# ============================
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("api:app", host="0.0.0.0", port=port)
