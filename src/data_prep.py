import os
import sys
import numpy as np
import pandas as pd
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def load_cleaned_data(results_path, ranking_path):
    """Loads cleaned match results and FIFA rankings."""
    if not os.path.exists(results_path) or not os.path.exists(ranking_path):
        logging.error("Cleaned data files missing. Please run verify_data.py first.")
        sys.exit(1)
    logging.info(f"Loading {results_path}...")
    df_results = pd.read_csv(results_path)
    logging.info(f"Loading {ranking_path}...")
    df_rankings = pd.read_csv(ranking_path)
    return df_results, df_rankings


def merge_fifa_rankings(df_matches, df_rankings):
    """
    Merges FIFA rankings for both home and away teams on the match date.
    Uses pd.merge_asof to match the closest ranking published strictly before the match date.
    Falls back to a default rank of 150.
    """
    logging.info("Merging FIFA rankings (lookahead-free)...")
    df_m = df_matches.copy()
    df_m["date"] = pd.to_datetime(df_m["date"])
    df_m = df_m.sort_values("date")
    df_m["original_index"] = df_m.index
    df_r = df_rankings.copy()
    rank_date_col = next(
        col for col in ["rank_date", "date", "ranking_date"] if col in df_r.columns
    )
    df_r["date"] = pd.to_datetime(df_r[rank_date_col])
    df_r = df_r.sort_values("date")
    df_r = df_r[["date", "country_full", "rank"]]
    df_home = pd.merge_asof(
        df_m,
        df_r,
        on="date",
        left_by="home_team",
        right_by="country_full",
        direction="backward",
        allow_exact_matches=False,
    )
    df_m["home_fifa_rank"] = df_home["rank"].fillna(150).astype(int)
    df_away = pd.merge_asof(
        df_m,
        df_r,
        on="date",
        left_by="away_team",
        right_by="country_full",
        direction="backward",
        allow_exact_matches=False,
    )
    df_m["away_fifa_rank"] = df_away["rank"].fillna(150).astype(int)
    df_m = df_m.set_index("original_index").sort_index()
    df_m["rank_difference"] = df_m["home_fifa_rank"] - df_m["away_fifa_rank"]
    return df_m


def compute_weighted_form_indices(df_matches, lambda_decay=0.001):
    """
    Computes custom weighted form index for Home and Away teams based on their last 100 matches.
    Also computes average goals scored in the last 5 matches.
    """
    logging.info("Computing custom weighted form indices and recent goals...")
    df_m = df_matches.copy()
    df_m["date"] = pd.to_datetime(df_m["date"])
    df_m["match_id"] = df_m.index
    history_records = []
    for idx, row in df_m.iterrows():
        home_score = row["home_score"]
        away_score = row["away_score"]
        if pd.isna(home_score) or pd.isna(away_score):
            continue
        if home_score > away_score:
            home_pts, away_pts = 3, 0
        elif home_score < away_score:
            home_pts, away_pts = 0, 3
        else:
            home_pts, away_pts = 1, 1
        history_records.append(
            {
                "match_id": row["match_id"],
                "date": row["date"],
                "team": row["home_team"],
                "opponent_rank": row["away_fifa_rank"],
                "points": home_pts,
                "is_home": 1,
                "goals_scored": home_score,
            }
        )
        history_records.append(
            {
                "match_id": row["match_id"],
                "date": row["date"],
                "team": row["away_team"],
                "opponent_rank": row["home_fifa_rank"],
                "points": away_pts,
                "is_home": 0,
                "goals_scored": away_score,
            }
        )
    df_hist = pd.DataFrame(history_records)
    df_hist = df_hist.sort_values("date")
    home_forms = {}
    away_forms = {}
    home_recent_goals = {}
    away_recent_goals = {}
    team_match_counts = {}
    for team, group in df_hist.groupby("team"):
        group = group.reset_index(drop=True)
        n_matches = len(group)
        dates = group["date"].values
        points = group["points"].values
        opp_ranks = group["opponent_rank"].values
        match_ids = group["match_id"].values
        is_homes = group["is_home"].values
        goals_scored = group["goals_scored"].values
        w_ranks = 1.0 + (np.clip(200 - opp_ranks, 0, None) / 200.0)
        for j in range(n_matches):
            current_match_id = match_ids[j]
            current_date = dates[j]
            is_home = is_homes[j]
            team_match_counts[(current_match_id, team)] = j
            start_idx = max(0, j - 100)
            if start_idx == j:
                form_index = 1.0
            else:
                hist_dates = dates[start_idx:j]
                hist_pts = points[start_idx:j]
                hist_w_ranks = w_ranks[start_idx:j]
                days_diff = (
                    (current_date - hist_dates).astype("timedelta64[D]").astype(float)
                )
                w_time = np.exp(-lambda_decay * days_diff)
                w_total = hist_w_ranks * w_time
                weighted_scores = hist_pts * w_total
                sum_w_total = np.sum(w_total)
                if sum_w_total > 0:
                    form_index = np.sum(weighted_scores) / sum_w_total
                else:
                    form_index = 1.0
            start_goals_idx = max(0, j - 5)
            if start_goals_idx == j:
                recent_goals = 1.3
            else:
                recent_goals = np.mean(goals_scored[start_goals_idx:j])
            if is_home:
                home_forms[current_match_id] = form_index
                home_recent_goals[current_match_id] = recent_goals
            else:
                away_forms[current_match_id] = form_index
                away_recent_goals[current_match_id] = recent_goals
    df_m["home_weighted_form"] = df_m["match_id"].map(home_forms)
    df_m["away_weighted_form"] = df_m["match_id"].map(away_forms)
    df_m["home_recent_goals_scored"] = df_m["match_id"].map(home_recent_goals)
    df_m["away_recent_goals_scored"] = df_m["match_id"].map(away_recent_goals)
    df_m["home_match_count"] = df_m.apply(
        lambda r: team_match_counts.get((r["match_id"], r["home_team"]), 0), axis=1
    )
    df_m["away_match_count"] = df_m.apply(
        lambda r: team_match_counts.get((r["match_id"], r["away_team"]), 0), axis=1
    )
    return df_m


def compute_h2h_features(df_matches):
    """
    Computes Head-to-Head (H2H) features for Home and Away teams.
    """
    logging.info("Computing Head-to-Head (H2H) features...")
    df_m = df_matches.copy()
    df_m["date"] = pd.to_datetime(df_m["date"])
    df_m["match_id"] = df_m.index

    def get_pair_key(row):
        t1, t2 = row["home_team"], row["away_team"]
        return (t1, t2) if t1 < t2 else (t2, t1)

    df_m["team_pair"] = df_m.apply(get_pair_key, axis=1)
    h2h_home_win_rates = {}
    h2h_away_win_rates = {}
    h2h_avg_goal_diffs = {}
    for pair, group in df_m.groupby("team_pair"):
        group = group.sort_values("date").reset_index(drop=True)
        n_matches = len(group)
        for j in range(n_matches):
            current_match = group.iloc[j]
            current_match_id = current_match["match_id"]
            current_home = current_match["home_team"]
            current_away = current_match["away_team"]
            hist_matches = group.iloc[0:j]
            if len(hist_matches) == 0:
                h2h_home_win_rates[current_match_id] = 0.33
                h2h_away_win_rates[current_match_id] = 0.33
                h2h_avg_goal_diffs[current_match_id] = 0.0
            else:
                wins_home = 0
                wins_away = 0
                goal_diff_sum = 0.0
                for _, hist in hist_matches.iterrows():
                    h_score = hist["home_score"]
                    a_score = hist["away_score"]
                    if pd.isna(h_score) or pd.isna(a_score):
                        continue
                    if hist["home_team"] == current_home:
                        g_diff = h_score - a_score
                        if h_score > a_score:
                            wins_home += 1
                        elif a_score > h_score:
                            wins_away += 1
                    else:
                        g_diff = a_score - h_score
                        if a_score > h_score:
                            wins_home += 1
                        elif h_score > a_score:
                            wins_away += 1
                    goal_diff_sum += g_diff
                total_valid = len(hist_matches)
                h2h_home_win_rates[current_match_id] = wins_home / total_valid
                h2h_away_win_rates[current_match_id] = wins_away / total_valid
                h2h_avg_goal_diffs[current_match_id] = goal_diff_sum / total_valid
    df_m["h2h_home_win_rate"] = df_m["match_id"].map(h2h_home_win_rates)
    df_m["h2h_away_win_rate"] = df_m["match_id"].map(h2h_away_win_rates)
    df_m["h2h_avg_goal_diff"] = df_m["match_id"].map(h2h_avg_goal_diffs)
    return df_m


def main():
    results_path = "data/results_cleaned.csv"
    ranking_path = "data/fifa_ranking_cleaned.csv"
    output_path = "data/processed_data.csv"
    df_results, df_rankings = load_cleaned_data(results_path, ranking_path)
    df_features = merge_fifa_rankings(df_results, df_rankings)
    df_features = compute_weighted_form_indices(df_features)
    df_features = compute_h2h_features(df_features)

    def get_outcome(row):
        h = row["home_score"]
        a = row["away_score"]
        if pd.isna(h) or pd.isna(a):
            return np.nan
        if h > a:
            return 2
        elif h < a:
            return 0
        else:
            return 1

    df_features["match_outcome"] = df_features.apply(get_outcome, axis=1)
    logging.info(
        "Filtering matches (minimum 5 previous matches played for both teams)..."
    )
    initial_shape = df_features.shape
    df_processed = df_features[
        (df_features["home_match_count"] >= 5) & (df_features["away_match_count"] >= 5)
    ].copy()
    logging.info(f"Filtered dataset from {initial_shape} to {df_processed.shape}")
    final_cols = [
        "date",
        "home_team",
        "away_team",
        "home_score",
        "away_score",
        "home_fifa_rank",
        "away_fifa_rank",
        "rank_difference",
        "home_weighted_form",
        "away_weighted_form",
        "home_recent_goals_scored",
        "away_recent_goals_scored",
        "h2h_home_win_rate",
        "h2h_away_win_rate",
        "h2h_avg_goal_diff",
        "match_outcome",
    ]
    df_processed = df_processed[final_cols].dropna()
    df_processed.to_csv(output_path, index=False)
    logging.info(f"Successfully processed features and saved to {output_path}")
    print("\nProcessed Dataset Sample Head:")
    print(df_processed.head())
    corr = df_processed[
        [
            "rank_difference",
            "match_outcome",
            "home_weighted_form",
            "away_weighted_form",
            "home_recent_goals_scored",
            "away_recent_goals_scored",
        ]
    ].corr()
    print("\nFeature Correlation Matrix:")
    print(corr)


if __name__ == "__main__":
    main()
