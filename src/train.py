import os
import sys
import pandas as pd
import numpy as np
import logging
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import PoissonRegressor
from sklearn.metrics import (
    accuracy_score,
    log_loss,
    mean_absolute_error,
    mean_squared_error,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def main():
    processed_data_path = "data/processed_data.csv"
    models_dir = "models"
    if not os.path.exists(processed_data_path):
        logging.error(
            f"Processed dataset not found at {processed_data_path}. Please run data_prep.py first."
        )
        sys.exit(1)
    os.makedirs(models_dir, exist_ok=True)
    logging.info(f"Loading processed dataset from {processed_data_path}...")
    df = pd.read_csv(processed_data_path)
    feature_cols = [
        "home_weighted_form",
        "away_weighted_form",
        "home_fifa_rank",
        "away_fifa_rank",
        "rank_difference",
        "h2h_home_win_rate",
        "h2h_avg_goal_diff",
        "home_recent_goals_scored",
        "away_recent_goals_scored",
    ]
    logging.info("Splitting dataset chronologically...")
    df["date"] = pd.to_datetime(df["date"])
    split_date = pd.to_datetime("2025-01-01")
    train_mask = df["date"] < split_date
    test_mask = df["date"] >= split_date
    df_train = df[train_mask]
    df_test = df[test_mask]
    logging.info(
        f"Train matches: {len(df_train)} (before {split_date.strftime('%Y-%m-%d')})"
    )
    logging.info(
        f"Test matches: {len(df_test)} (on/after {split_date.strftime('%Y-%m-%d')})"
    )
    if len(df_test) == 0:
        logging.warning(
            "Test dataset is empty. Using random split fallback for validation prints, but training on all data..."
        )
        from sklearn.model_selection import train_test_split

        df_train, df_test = train_test_split(df, test_size=0.2, random_state=42)
        logging.info(f"Fallback split: Train={len(df_train)}, Test={len(df_test)}")
    X_train = df_train[feature_cols]
    X_test = df_test[feature_cols]
    y_class_train = df_train["match_outcome"].astype(int)
    y_class_test = df_test["match_outcome"].astype(int)
    y_home_goals_train = df_train["home_score"]
    y_home_goals_test = df_test["home_score"]
    y_away_goals_train = df_train["away_score"]
    y_away_goals_test = df_test["away_score"]
    logging.info("Fitting and applying StandardScaler...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    logging.info("Training Calibrated Outcome Classifier (1X2)...")
    base_clf = GradientBoostingClassifier(
        n_estimators=100, learning_rate=0.05, max_depth=3, random_state=42
    )
    calibrated_clf = CalibratedClassifierCV(estimator=base_clf, method="sigmoid", cv=5)
    calibrated_clf.fit(X_train_scaled, y_class_train)
    base_clf.fit(X_train_scaled, y_class_train)
    logging.info("Training Home & Away Goal Poisson Regressors...")
    home_goals_model = PoissonRegressor(alpha=1.0, max_iter=300)
    home_goals_model.fit(X_train_scaled, y_home_goals_train)
    away_goals_model = PoissonRegressor(alpha=1.0, max_iter=300)
    away_goals_model.fit(X_train_scaled, y_away_goals_train)
    logging.info("=" * 50)
    logging.info("MODEL EVALUATION")
    logging.info("=" * 50)
    y_class_pred = calibrated_clf.predict(X_test_scaled)
    y_class_proba = calibrated_clf.predict_proba(X_test_scaled)
    accuracy = accuracy_score(y_class_test, y_class_pred)
    loss = log_loss(y_class_test, y_class_proba)
    logging.info(f"Classifier Accuracy: {accuracy:.4f}")
    logging.info(f"Classifier Multi-class Log-Loss: {loss:.4f}")
    y_home_pred = home_goals_model.predict(X_test_scaled)
    y_away_pred = away_goals_model.predict(X_test_scaled)
    home_mae = mean_absolute_error(y_home_goals_test, y_home_pred)
    home_mse = mean_squared_error(y_home_goals_test, y_home_pred)
    away_mae = mean_absolute_error(y_away_goals_test, y_away_pred)
    away_mse = mean_squared_error(y_away_goals_test, y_away_pred)
    logging.info(f"Home Goals Regressor - MAE: {home_mae:.4f}, MSE: {home_mse:.4f}")
    logging.info(f"Away Goals Regressor - MAE: {away_mae:.4f}, MSE: {away_mse:.4f}")
    importances = base_clf.feature_importances_
    logging.info("-" * 30)
    logging.info("Feature Importances (Base GBDT Classifier):")
    for feat, imp in sorted(
        zip(feature_cols, importances), key=lambda x: x[1], reverse=True
    ):
        logging.info(f"  {feat}: {imp:.4f}")
    logging.info("-" * 30)
    logging.info("Saving trained models and scaler...")
    joblib.dump(scaler, os.path.join(models_dir, "scaler.joblib"))
    joblib.dump(calibrated_clf, os.path.join(models_dir, "outcome_classifier.joblib"))
    joblib.dump(
        home_goals_model, os.path.join(models_dir, "home_goals_regressor.joblib")
    )
    joblib.dump(
        away_goals_model, os.path.join(models_dir, "away_goals_regressor.joblib")
    )
    logging.info("All artifacts successfully saved to '/models' directory.")


if __name__ == "__main__":
    main()
