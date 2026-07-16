import os
import sys
import pandas as pd
import numpy as np
import joblib
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

app = FastAPI(title="Football Match Predictor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scaler = None

outcome_classifier = None

home_goals_regressor = None

away_goals_regressor = None

df_processed = None

unique_teams = []


@app.on_event("startup")
def startup_event():
    global scaler, outcome_classifier, home_goals_regressor, away_goals_regressor, df_processed, unique_teams
    models_dir = "models"
    processed_data_path = "data/processed_data.csv"
    required_models = {
        "scaler": os.path.join(models_dir, "scaler.joblib"),
        "outcome_classifier": os.path.join(models_dir, "outcome_classifier.joblib"),
        "home_goals_regressor": os.path.join(models_dir, "home_goals_regressor.joblib"),
        "away_goals_regressor": os.path.join(models_dir, "away_goals_regressor.joblib"),
    }
    missing_models = [
        name for name, path in required_models.items() if not os.path.exists(path)
    ]
    if missing_models:
        logging.error(
            f"Missing trained model files: {missing_models}. Please run src/train.py first."
        )
        return
    if not os.path.exists(processed_data_path):
        logging.error(
            f"Processed dataset not found at {processed_data_path}. Please run src/data_prep.py first."
        )
        return
    try:
        logging.info("Loading trained models and scaler...")
        scaler = joblib.load(required_models["scaler"])
        outcome_classifier = joblib.load(required_models["outcome_classifier"])
        home_goals_regressor = joblib.load(required_models["home_goals_regressor"])
        away_goals_regressor = joblib.load(required_models["away_goals_regressor"])
        logging.info("Loading processed dataset...")
        df_processed = pd.read_csv(processed_data_path)
        df_processed["date"] = pd.to_datetime(df_processed["date"])
        df_processed = df_processed.sort_values("date")
        home_set = set(df_processed["home_team"].unique())
        away_set = set(df_processed["away_team"].unique())
        unique_teams = sorted(list(home_set.union(away_set)))
        logging.info(f"Loaded {len(unique_teams)} unique teams successfully.")
    except Exception as e:
        logging.error(f"Error during startup data/model loading: {e}")


class PredictionRequest(BaseModel):
    team1: str
    team2: str
    neutral: bool = False


@app.get("/")
def read_root():
    return FileResponse("static/index.html")


@app.get("/api/teams")
def get_teams():
    if df_processed is None:
        raise HTTPException(
            status_code=503,
            detail="Server not fully initialized. Models or datasets are missing.",
        )
    return unique_teams


def resolve_team_stats(team_name: str):
    """
    Finds the most recent row in the dataset where the team appeared (either as home or away)
    to extract its latest weighted form, latest FIFA rank, and latest recent goals scored.
    """
    team_matches = df_processed[
        (df_processed["home_team"] == team_name)
        | (df_processed["away_team"] == team_name)
    ]
    if len(team_matches) == 0:
        return 1.0, 150, 1.3
    latest_match = team_matches.iloc[-1]
    if latest_match["home_team"] == team_name:
        form = latest_match["home_weighted_form"]
        rank = latest_match["home_fifa_rank"]
        recent_goals = latest_match["home_recent_goals_scored"]
    else:
        form = latest_match["away_weighted_form"]
        rank = latest_match["away_fifa_rank"]
        recent_goals = latest_match["away_recent_goals_scored"]
    return float(form), int(rank), float(recent_goals)


def resolve_h2h_stats(team_a: str, team_b: str):
    """
    Calculates dynamic head-to-head metrics from Team A's perspective.
    Returns: (h2h_home_win_rate, h2h_avg_goal_diff)
    """
    h2h_matches = df_processed[
        ((df_processed["home_team"] == team_a) & (df_processed["away_team"] == team_b))
        | (
            (df_processed["home_team"] == team_b)
            & (df_processed["away_team"] == team_a)
        )
    ]
    if len(h2h_matches) == 0:
        return 0.33, 0.0
    wins_a = 0
    goal_diff_sum = 0.0
    for _, match in h2h_matches.iterrows():
        h_score = match["home_score"]
        a_score = match["away_score"]
        if match["home_team"] == team_a:
            goal_diff = h_score - a_score
            if h_score > a_score:
                wins_a += 1
        else:
            goal_diff = a_score - h_score
            if a_score > h_score:
                wins_a += 1
        goal_diff_sum += goal_diff
    total = len(h2h_matches)
    win_rate = wins_a / total
    avg_goal_diff = goal_diff_sum / total
    return float(win_rate), float(avg_goal_diff)


def run_single_perspective(team_home: str, team_away: str):
    """
    Runs match simulation features and models for a single asymmetric home-away perspective.
    """
    home_weighted_form, home_fifa_rank, home_recent_goals = resolve_team_stats(
        team_home
    )
    away_weighted_form, away_fifa_rank, away_recent_goals = resolve_team_stats(
        team_away
    )
    rank_difference = home_fifa_rank - away_fifa_rank
    h2h_home_win_rate, h2h_avg_goal_diff = resolve_h2h_stats(team_home, team_away)
    feature_vector = np.array(
        [
            [
                home_weighted_form,
                away_weighted_form,
                home_fifa_rank,
                away_fifa_rank,
                rank_difference,
                h2h_home_win_rate,
                h2h_avg_goal_diff,
                home_recent_goals,
                away_recent_goals,
            ]
        ]
    )
    feature_vector_scaled = scaler.transform(feature_vector)
    proba = outcome_classifier.predict_proba(feature_vector_scaled)[0]
    pred_home_goals = home_goals_regressor.predict(feature_vector_scaled)[0]
    pred_away_goals = away_goals_regressor.predict(feature_vector_scaled)[0]
    return proba, pred_home_goals, pred_away_goals


@app.post("/api/predict")
def predict_match(payload: PredictionRequest):
    if df_processed is None or outcome_classifier is None:
        raise HTTPException(
            status_code=503, detail="Model and dataset state not loaded on server."
        )
    team1 = payload.team1.strip()
    team2 = payload.team2.strip()
    if team1 not in unique_teams:
        raise HTTPException(
            status_code=400,
            detail=f"Team '{team1}' not found in the historical dataset.",
        )
    if team2 not in unique_teams:
        raise HTTPException(
            status_code=400,
            detail=f"Team '{team2}' not found in the historical dataset.",
        )
    if team1 == team2:
        raise HTTPException(
            status_code=400, detail="Home team and Away team cannot be the same."
        )
    if not payload.neutral:
        proba, pred_home_goals, pred_away_goals = run_single_perspective(team1, team2)
        raw_pct = [proba[2] * 100.0, proba[1] * 100.0, proba[0] * 100.0]
        home_score_val = pred_home_goals
        away_score_val = pred_away_goals
    else:
        proba_1, goals_home_1, goals_away_1 = run_single_perspective(team1, team2)
        proba_2, goals_home_2, goals_away_2 = run_single_perspective(team2, team1)
        p1 = (proba_1[2] + proba_2[0]) / 2.0 * 100.0
        pd = (proba_1[1] + proba_2[1]) / 2.0 * 100.0
        p2 = (proba_1[0] + proba_2[2]) / 2.0 * 100.0
        raw_pct = [p1, pd, p2]
        home_score_val = (goals_home_1 + goals_away_2) / 2.0
        away_score_val = (goals_away_1 + goals_home_2) / 2.0
    rounded_pct = [int(round(p)) for p in raw_pct]
    diff = 100 - sum(rounded_pct)
    if diff != 0:
        max_idx = rounded_pct.index(max(rounded_pct))
        rounded_pct[max_idx] += diff
    home_score_pred = int(round(home_score_val))
    away_score_pred = int(round(away_score_val))
    home_score_pred = max(0, home_score_pred)
    away_score_pred = max(0, away_score_pred)
    return {
        "status": "success",
        "matchup": {"home_team": team1, "away_team": team2, "neutral": payload.neutral},
        "probabilities": {
            "team1": rounded_pct[0],
            "draw": rounded_pct[1],
            "team2": rounded_pct[2],
        },
        "predicted_score": {"team1": home_score_pred, "team2": away_score_pred},
    }


app.mount("/", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
