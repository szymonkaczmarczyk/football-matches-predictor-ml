import os
import sys
import pandas as pd
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

COUNTRY_NAME_TRANSLATION = {
    "USA": "United States",
    "US": "United States",
    "Korea Republic": "South Korea",
    "South Korea": "South Korea",
    "Korea, South": "South Korea",
    "IR Iran": "Iran",
    "Iran, Islamic Republic of": "Iran",
    "Côte d'Ivoire": "Ivory Coast",
    "Cote d'Ivoire": "Ivory Coast",
    "DR Congo": "Congo DR",
    "Democratic Republic of the Congo": "Congo DR",
    "Congo, Democratic Republic of the": "Congo DR",
    "Cabo Verde": "Cape Verde",
    "Türkiye": "Turkey",
    "Saint Kitts and Nevis": "St. Kitts and Nevis",
    "St. Kitts & Nevis": "St. Kitts and Nevis",
    "Saint Vincent and the Grenadines": "St. Vincent and the Grenadines",
    "St. Vincent & Grenadines": "St. Vincent and the Grenadines",
    "Curacao": "Curaçao",
    "Czechia": "Czech Republic",
    "Kyrgyzstan": "Kyrgyz Republic",
}


def verify_and_clean_data(results_path, ranking_path):
    missing_files = []
    if not os.path.exists(results_path):
        missing_files.append(results_path)
    if not os.path.exists(ranking_path):
        missing_files.append(ranking_path)
    if missing_files:
        logging.error("Missing raw data files!")
        for file in missing_files:
            logging.error(f"  - File not found: {file}")
        logging.info(
            "Please download the Kaggle datasets and place them in the 'data/' directory."
        )
        logging.info(
            "Expected files:\n  - results.csv (Match history)\n  - fifa_ranking.csv (FIFA rankings)"
        )
        return False
    logging.info(f"Loading data from {results_path}...")
    try:
        df_results = pd.read_csv(results_path)
    except Exception as e:
        logging.error(f"Error reading {results_path}: {e}")
        return False
    logging.info(f"Loading data from {ranking_path}...")
    try:
        df_rankings = pd.read_csv(ranking_path)
    except Exception as e:
        logging.error(f"Error reading {ranking_path}: {e}")
        return False
    logging.info("=" * 50)
    logging.info("DIAGNOSTICS & METADATA")
    logging.info("=" * 50)
    results_mem = df_results.memory_usage(deep=True).sum() / (1024 * 1024)
    logging.info(f"results.csv Shape: {df_results.shape}")
    logging.info(f"results.csv Memory Usage: {results_mem:.2f} MB")
    logging.info(f"results.csv Columns: {list(df_results.columns)}")
    rankings_mem = df_rankings.memory_usage(deep=True).sum() / (1024 * 1024)
    logging.info(f"fifa_ranking.csv Shape: {df_rankings.shape}")
    logging.info(f"fifa_ranking.csv Memory Usage: {rankings_mem:.2f} MB")
    logging.info(f"fifa_ranking.csv Columns: {list(df_rankings.columns)}")
    results_date_col = "date" if "date" in df_results.columns else None
    rankings_date_col = None
    for col in ["date", "rank_date", "ranking_date"]:
        if col in df_rankings.columns:
            rankings_date_col = col
            break
    if results_date_col:
        temp_date = pd.to_datetime(df_results[results_date_col], errors="coerce")
        min_date, max_date = temp_date.min(), temp_date.max()
        logging.info(
            f"results.csv Date Range: {min_date.strftime('%Y-%m-%d') if pd.notnull(min_date) else 'N/A'} to {max_date.strftime('%Y-%m-%d') if pd.notnull(max_date) else 'N/A'}"
        )
    else:
        logging.warning("No date column found in results.csv")
    if rankings_date_col:
        temp_date = pd.to_datetime(df_rankings[rankings_date_col], errors="coerce")
        min_date, max_date = temp_date.min(), temp_date.max()
        logging.info(
            f"fifa_ranking.csv Date Range: {min_date.strftime('%Y-%m-%d') if pd.notnull(min_date) else 'N/A'} to {max_date.strftime('%Y-%m-%d') if pd.notnull(max_date) else 'N/A'}"
        )
    else:
        logging.warning("No date column found in fifa_ranking.csv")
    logging.info("=" * 50)
    logging.info("MISSING VALUES CHECK")
    logging.info("=" * 50)
    res_critical = ["home_team", "away_team", "home_score", "away_score"]
    for col in res_critical:
        if col in df_results.columns:
            missing = df_results[col].isnull().sum()
            logging.info(f"results.csv -> '{col}' missing values: {missing}")
        else:
            logging.warning(f"results.csv -> Critical column '{col}' missing!")
    rank_critical = ["country_full", "rank"]
    for col in rank_critical:
        if col in df_rankings.columns:
            missing = df_rankings[col].isnull().sum()
            logging.info(f"fifa_ranking.csv -> '{col}' missing values: {missing}")
        else:
            logging.warning(f"fifa_ranking.csv -> Critical column '{col}' missing!")
    logging.info("=" * 50)
    logging.info("DATA CLEANING")
    logging.info("=" * 50)
    if results_date_col:
        logging.info(f"Converting '{results_date_col}' in results to datetime...")
        df_results[results_date_col] = pd.to_datetime(
            df_results[results_date_col], errors="coerce"
        )
        df_results = df_results.dropna(subset=[results_date_col])
        df_results[results_date_col] = df_results[results_date_col].dt.strftime(
            "%Y-%m-%d"
        )
    if rankings_date_col:
        logging.info(f"Converting '{rankings_date_col}' in rankings to datetime...")
        df_rankings[rankings_date_col] = pd.to_datetime(
            df_rankings[rankings_date_col], errors="coerce"
        )
        df_rankings = df_rankings.dropna(subset=[rankings_date_col])
        df_rankings[rankings_date_col] = df_rankings[rankings_date_col].dt.strftime(
            "%Y-%m-%d"
        )
    home_teams = (
        set(df_results["home_team"].dropna().unique())
        if "home_team" in df_results.columns
        else set()
    )
    away_teams = (
        set(df_results["away_team"].dropna().unique())
        if "away_team" in df_results.columns
        else set()
    )
    results_countries = home_teams.union(away_teams)
    rankings_countries = (
        set(df_rankings["country_full"].dropna().unique())
        if "country_full" in df_rankings.columns
        else set()
    )
    logging.info(f"Unique countries in results.csv: {len(results_countries)}")
    logging.info(f"Unique countries in fifa_ranking.csv: {len(rankings_countries)}")
    unmatched_results = results_countries - rankings_countries
    logging.info(
        f"Initial unmatched teams in results (not found in rankings): {len(unmatched_results)}"
    )

    def standardize_team_name(name):
        if not isinstance(name, str):
            return name
        name_stripped = name.strip()
        return COUNTRY_NAME_TRANSLATION.get(name_stripped, name_stripped)

    logging.info("Applying team/country name standardization...")
    if "home_team" in df_results.columns:
        df_results["home_team"] = df_results["home_team"].apply(standardize_team_name)
    if "away_team" in df_results.columns:
        df_results["away_team"] = df_results["away_team"].apply(standardize_team_name)
    if "country_full" in df_rankings.columns:
        df_rankings["country_full"] = df_rankings["country_full"].apply(
            standardize_team_name
        )
    home_teams_new = (
        set(df_results["home_team"].dropna().unique())
        if "home_team" in df_results.columns
        else set()
    )
    away_teams_new = (
        set(df_results["away_team"].dropna().unique())
        if "away_team" in df_results.columns
        else set()
    )
    results_countries_new = home_teams_new.union(away_teams_new)
    rankings_countries_new = (
        set(df_rankings["country_full"].dropna().unique())
        if "country_full" in df_rankings.columns
        else set()
    )
    unmatched_results_new = results_countries_new - rankings_countries_new
    logging.info(
        f"Unmatched teams in results after standardization: {len(unmatched_results_new)}"
    )
    out_results_path = results_path.replace(".csv", "_cleaned.csv")
    out_rankings_path = ranking_path.replace(".csv", "_cleaned.csv")
    df_results.to_csv(out_results_path, index=False)
    df_rankings.to_csv(out_rankings_path, index=False)
    logging.info(f"Saved cleaned results to {out_results_path}")
    logging.info(f"Saved cleaned rankings to {out_rankings_path}")
    return True


if __name__ == "__main__":
    verify_and_clean_data("data/results.csv", "data/fifa_ranking.csv")
