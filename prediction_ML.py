# football_ml_pipeline.py
# Clean, modular pipeline for classification (result) and regression (goals) on football matches.
# - Loads Excel/CSV
# - Normalizes column names
# - Handles missing values
# - Encodes teams (OneHot)
# - Scales numerical features
# - Trains RF/XGBoost classifiers & regressors
# - Evaluates with Accuracy, F1, Confusion Matrix (classification) and MAE, RMSE (regression)
# - Prints example predictions

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    confusion_matrix,
    classification_report,
    mean_absolute_error,
    mean_squared_error,
)
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor

# Optional XGBoost (falls back to RF if not installed)
try:
    from xgboost import XGBClassifier, XGBRegressor
    HAS_XGB = True
except Exception:
    HAS_XGB = False
    XGBClassifier = None
    XGBRegressor = None


# ---------------------------
# Configuration and features
# ---------------------------

@dataclass
class Config:
    # Input
    filepath: str = "enhanced_football_matches.xlsx"  # change to dataset path
    sheet_name: Optional[str] = "Matches"  # None for CSV or a specific sheet for Excel

    # Modeling
    test_size: float = 0.2
    random_state: int = 42
    clf_model: str = "rf"  # "rf" or "xgb"
    reg_model: str = "rf"  # "rf" or "xgb"

    # Display
    n_example_predictions: int = 5


# Normalization map for frequently seen variants
COLUMN_NORMALIZATION_MAP = {
    # Date
    "date": "match_date",
    "matchdate": "match_date",

    # Teams
    "home_team": "home_team",
    "away_team": "away_team",

    # Last 5 points
    "home_last5_points": "home_points_last5",
    "away_last5_points": "away_points_last5",

    # Last 5 goals scored
    "home_last5_goals_scored": "home_goals_scored_last5",
    "away_last5_goals_scored": "away_goals_scored_last5",

    # Last 5 goals conceded
    "home_last5_goals_conceded": "home_goals_conceded_last5",
    "away_last5_goals_conceded": "away_goals_conceded_last5",

    # League position
    "home_league_position": "home_league_position",
    "away_league_position": "away_league_position",

    # Head-to-head
    "head_to_head_wins_home": "h2h_wins_home",
    "head_to_head_wins_away": "h2h_wins_away",

    # Targets
    "home_goals": "home_goals",
    "away_goals": "away_goals",
    "result": "result",

    # Sometimes provided
    "final_score": "final_score",
    "match_status": "match_status",
    "is_completed": "is_completed",
    "goal_difference_home": "goal_difference_home",
    "goal_difference_away": "goal_difference_away",
}


# ---------------------------------
# Data loading and preprocessing
# ---------------------------------

def load_dataset(cfg: Config) -> pd.DataFrame:
    # Load Excel or CSV based on file extension
    if cfg.filepath.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(cfg.filepath, sheet_name=cfg.sheet_name)
    elif cfg.filepath.lower().endswith(".csv"):
        df = pd.read_csv(cfg.filepath)
    else:
        raise ValueError("Unsupported file format; please provide .csv or .xlsx")
    return df


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names to a consistent set used downstream.
    """
    new_cols = {}
    for c in df.columns:
        key = c.strip().lower().replace(" ", "_")
        mapped = COLUMN_NORMALIZATION_MAP.get(key, key)
        new_cols[c] = mapped
    df = df.rename(columns=new_cols)
    return df


def parse_final_score_to_goals(df: pd.DataFrame) -> pd.DataFrame:
    """
    If home_goals/away_goals not present, try to parse from 'final_score' like '2-1'.
    Only for completed matches where possible.
    """
    if "home_goals" in df.columns and "away_goals" in df.columns:
        return df

    if "final_score" not in df.columns:
        return df

    # Create empty columns if not present
    if "home_goals" not in df.columns:
        df["home_goals"] = np.nan
    if "away_goals" not in df.columns:
        df["away_goals"] = np.nan

    pattern = re.compile(r"^\s*(\d+)\s*[-:x]\s*(\d+)\s*$", re.IGNORECASE)
    mask = df["final_score"].notna()
    for idx in df[mask].index:
        s = str(df.at[idx, "final_score"])
        m = pattern.match(s)
        if m:
            df.at[idx, "home_goals"] = float(m.group(1))
            df.at[idx, "away_goals"] = float(m.group(2))

    return df


def derive_result(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure 'result' exists from home_goals vs away_goals (H/D/A).
    """
    if "result" in df.columns:
        return df

    if "home_goals" in df.columns and "away_goals" in df.columns:
        def to_result(row):
            try:
                hg = float(row["home_goals"])
                ag = float(row["away_goals"])
            except Exception:
                return np.nan
            if np.isnan(hg) or np.isnan(ag):
                return np.nan
            if hg > ag:
                return "H"
            elif hg < ag:
                return "A"
            else:
                return "D"

        df["result"] = df.apply(to_result, axis=1)

    return df


def add_date_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert match_date to datetime and extract day-of-week and month.
    """
    if "match_date" in df.columns:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df["match_date"] = pd.to_datetime(df["match_date"], errors="coerce", utc=True)
        df["match_dayofweek"] = df["match_date"].dt.weekday
        df["match_month"] = df["match_date"].dt.month
    return df


def select_feature_sets(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """
    Identify categorical and numerical features based on availability.
    """
    categorical = [c for c in ["home_team", "away_team"] if c in df.columns]

    numeric_candidates = [
        "home_points_last5",
        "home_goals_scored_last5",
        "home_goals_conceded_last5",
        "home_league_position",
        "away_points_last5",
        "away_goals_scored_last5",
        "away_goals_conceded_last5",
        "away_league_position",
        "h2h_wins_home",
        "h2h_wins_away",
        "goal_difference_home",
        "goal_difference_away",
        "match_dayofweek",
        "match_month",
    ]
    numeric = [c for c in numeric_candidates if c in df.columns]
    return categorical, numeric


def build_preprocessor(categorical: List[str], numeric: List[str]) -> ColumnTransformer:
    """
    ColumnTransformer that imputes and encodes categorical, imputes and scales numeric.
    """
    cat_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=True)),
    ])

    num_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", cat_pipeline, categorical),
            ("num", num_pipeline, numeric),
        ],
        remainder="drop",
        sparse_threshold=0.3,
    )
    return preprocessor


# ---------------------------
# Modeling helpers
# ---------------------------

def get_classifier(model_type: str, random_state: int):
    if model_type == "xgb" and HAS_XGB:
        return XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.0,
            objective="multi:softprob",
            eval_metric="mlogloss",
            random_state=random_state,
            tree_method="hist",
        )
    # Fallback RF
    return RandomForestClassifier(
        n_estimators=400,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        n_jobs=-1,
        random_state=random_state,
        class_weight="balanced_subsample",
    )


def get_regressor(model_type: str, random_state: int):
    if model_type == "xgb" and HAS_XGB:
        base = XGBRegressor(
            n_estimators=350,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.0,
            objective="reg:squarederror",
            random_state=random_state,
            tree_method="hist",
        )
    else:
        base = RandomForestRegressor(
            n_estimators=400,
            max_depth=None,
            min_samples_split=2,
            min_samples_leaf=1,
            n_jobs=-1,
            random_state=random_state,
        )
    # Multi-output wrapper to predict [home_goals, away_goals]
    return MultiOutputRegressor(base)


def evaluate_classification(y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, object]:
    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average="macro")
    cm = confusion_matrix(y_true, y_pred, labels=["H", "D", "A"])
    report = classification_report(y_true, y_pred, digits=3)
    return {"accuracy": acc, "f1_macro": f1, "confusion_matrix": cm, "report": report}


def evaluate_regression(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    y_true and y_pred are shape (n_samples, 2) for [home_goals, away_goals].
    Report per-target and overall averages.
    """
    mae_home = mean_absolute_error(y_true[:, 0], y_pred[:, 0])
    mae_away = mean_absolute_error(y_true[:, 1], y_pred[:, 1])
    rmse_home = mean_squared_error(y_true[:, 0], y_pred[:, 0], squared=False)
    rmse_away = mean_squared_error(y_true[:, 1], y_pred[:, 1], squared=False)

    mae_avg = (mae_home + mae_away) / 2.0
    rmse_avg = (rmse_home + rmse_away) / 2.0

    return {
        "mae_home": mae_home,
        "mae_away": mae_away,
        "mae_avg": mae_avg,
        "rmse_home": rmse_home,
        "rmse_away": rmse_away,
        "rmse_avg": rmse_avg,
    }


def make_prediction_frame(
    X_sample: pd.DataFrame,
    y_true_cls: Optional[pd.Series],
    y_pred_cls: Optional[np.ndarray],
    y_true_reg: Optional[np.ndarray],
    y_pred_reg: Optional[np.ndarray],
    n: int = 5,
) -> pd.DataFrame:
    n = min(n, len(X_sample))
    out = pd.DataFrame(index=X_sample.index[:n])
    if y_true_cls is not None:
        out["true_result"] = y_true_cls.iloc[:n].values
    if y_pred_cls is not None:
        out["pred_result"] = y_pred_cls[:n]
    if y_true_reg is not None:
        out["true_home_goals"] = np.round(y_true_reg[:n, 0], 2)
        out["true_away_goals"] = np.round(y_true_reg[:n, 1], 2)
    if y_pred_reg is not None:
        out["pred_home_goals"] = np.round(y_pred_reg[:n, 0], 2)
        out["pred_away_goals"] = np.round(y_pred_reg[:n, 1], 2)
    return out.reset_index(drop=True)


# ---------------------------
# End-to-end runner
# ---------------------------

def main(cfg: Config):
    # 1) Load
    df = load_dataset(cfg)

    # 2) Normalize
    df = normalize_columns(df)

    # 3) Parse goals if needed
    df = parse_final_score_to_goals(df)
    df = derive_result(df)

    # 4) Date features
    df = add_date_features(df)

    # 5) Keep only rows with targets for training
    has_goals = ("home_goals" in df.columns) and ("away_goals" in df.columns)
    has_result = ("result" in df.columns)

    if not has_result and not has_goals:
        raise ValueError(
            "No targets found. Please ensure home_goals/away_goals exist or a parsable final_score for completed matches."
        )

    # If match_status/is_completed exist, optionally filter completed matches
    if "is_completed" in df.columns:
        df = df[df["is_completed"] == True].copy()

    # Drop rows with missing targets
    if has_result:
        df = df[df["result"].isin(["H", "D", "A"])]
    if has_goals:
        df = df[~df[["home_goals", "away_goals"]].isna().any(axis=1)]

    if len(df) < 10:
        warnings.warn("Very few labeled rows available; metrics may be unreliable.")

    # 6) Feature selection
    categorical, numeric = select_feature_sets(df)
    feature_cols = categorical + numeric

    # Minimal checks
    required_cats = {"home_team", "away_team"}
    if not required_cats.issubset(set(categorical)):
        warnings.warn("home_team/away_team not both present; results may degrade.")

    if len(feature_cols) == 0:
        raise ValueError("No usable feature columns were found after normalization.")

    # 7) Split
    X = df[feature_cols].copy()

    # Targets
    y_cls = df["result"] if has_result else None
    y_reg = df[["home_goals", "away_goals"]].values if has_goals else None

    # For classification split with stratify when available
    if y_cls is not None and len(np.unique(y_cls)) > 1:
        X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(
            X, y_cls, test_size=cfg.test_size, random_state=cfg.random_state, stratify=y_cls
        )
    else:
        X_train_c = X_test_c = y_train_c = y_test_c = None

    # For regression split
    if y_reg is not None:
        X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(
            X, y_reg, test_size=cfg.test_size, random_state=cfg.random_state
        )
    else:
        X_train_r = X_test_r = y_train_r = y_test_r = None

    # 8) Build preprocessors
    preprocessor = build_preprocessor(categorical, numeric)

    # 9) Classification pipeline
    clf_pipeline = None
    clf_metrics = None
    y_pred_cls = None

    if X_train_c is not None:
        clf_estimator = get_classifier(cfg.clf_model, cfg.random_state)
        clf_pipeline = Pipeline(steps=[
            ("preprocess", preprocessor),
            ("model", clf_estimator),
        ])
        clf_pipeline.fit(X_train_c, y_train_c)
        y_pred_cls = clf_pipeline.predict(X_test_c)
        clf_metrics = evaluate_classification(y_test_c, y_pred_cls)

    # 10) Regression pipeline
    reg_pipeline = None
    reg_metrics = None
    y_pred_reg = None

    if X_train_r is not None:
        reg_estimator = get_regressor(cfg.reg_model, cfg.random_state)
        reg_pipeline = Pipeline(steps=[
            ("preprocess", preprocessor),
            ("model", reg_estimator),
        ])
        reg_pipeline.fit(X_train_r, y_train_r)
        y_pred_reg = reg_pipeline.predict(X_test_r)
        reg_metrics = evaluate_regression(y_test_r, y_pred_reg)

    # 11) Print results
    print("\n=== Configuration ===")
    print(cfg)

    if clf_metrics is not None:
        print("\n=== Classification (Result: H/D/A) ===")
        print(f"Accuracy: {clf_metrics['accuracy']:.4f}")
        print(f"F1-macro: {clf_metrics['f1_macro']:.4f}")
        print("Confusion Matrix (rows=true, cols=pred) [H D A]:")
        print(clf_metrics["confusion_matrix"])
        print("\nClassification Report:")
        print(clf_metrics["report"])

        # Examples
        examples_cls = make_prediction_frame(
            X_test_c, y_test_c, y_pred_cls, None, None, n=cfg.n_example_predictions
        )
        print("\nExample classification predictions:")
        print(examples_cls)

    if reg_metrics is not None:
        print("\n=== Regression (Home/Away Goals) ===")
        print(f"MAE (home): {reg_metrics['mae_home']:.4f}")
        print(f"MAE (away): {reg_metrics['mae_away']:.4f}")
        print(f"MAE (avg):  {reg_metrics['mae_avg']:.4f}")
        print(f"RMSE (home): {reg_metrics['rmse_home']:.4f}")
        print(f"RMSE (away): {reg_metrics['rmse_away']:.4f}")
        print(f"RMSE (avg):  {reg_metrics['rmse_avg']:.4f}")

        # Examples
        examples_reg = make_prediction_frame(
            X_test_r, None, None, y_test_r, y_pred_reg, n=cfg.n_example_predictions
        )
        # Optionally add a derived result from regression predictions
        def pred_result_from_goals(hr, ar):
            if hr > ar:
                return "H"
            elif hr < ar:
                return "A"
            return "D"
        if "pred_home_goals" in examples_reg.columns:
            examples_reg["pred_result_from_reg"] = [
                pred_result_from_goals(hr, ar)
                for hr, ar in zip(examples_reg["pred_home_goals"], examples_reg["pred_away_goals"])
            ]
        print("\nExample regression predictions:")
        print(examples_reg)

    if clf_metrics is None and reg_metrics is None:
        raise ValueError("No trainable task found. Ensure at least classification or regression targets are present.")

    print("\nDone.")


if __name__ == "__main__":
    # Edit defaults here as needed
    cfg = Config(
        filepath="enhanced_football_matches.xlsx",  # or path/to/your_data.csv
        sheet_name="Matches",  # None for CSV
        test_size=0.2,
        random_state=42,
        clf_model="rf",  # "rf" or "xgb"
        reg_model="rf",  # "rf" or "xgb"
    )
    main(cfg)
