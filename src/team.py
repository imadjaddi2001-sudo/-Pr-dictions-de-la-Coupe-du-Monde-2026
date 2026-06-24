"""
Group stage simulation for World Cup 2026 (12 groups × 4 teams).
Generates all group fixtures, simulates results, and ranks teams.
"""
import pandas as pd
import numpy as np
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Tuple

from src.predictor import load_team_data, predict_match, simulate_match_result

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def load_groups() -> Dict[str, List[str]]:
    """Load group composition from reference CSV."""
    path = DATA_DIR / "reference" / "group_stages.csv"
    df = pd.read_csv(path, sep=";")
    groups = {}
    for group, gdf in df.groupby("group"):
        groups[str(group)] = gdf["nation"].tolist()
    return groups


def generate_group_fixtures(groups: Dict[str, List[str]]) -> pd.DataFrame:
    """Generate round-robin fixtures for each group."""
    rows = []
    match_num = 1
    for group, teams in sorted(groups.items()):
        for home, away in combinations(teams, 2):
            rows.append({
                "match_id": f"G{match_num:03d}",
                "group": group,
                "home_team": home,
                "away_team": away,
                "stage": "Group Stage",
            })
            match_num += 1
    return pd.DataFrame(rows)


def simulate_group_stage(n_simulations: int = 1) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Simulate the group stage once (or average over n_simulations).
    Returns (group_tables, match_results).
    """
    team_data = load_team_data()
    groups = load_groups()
    fixtures = generate_group_fixtures(groups)

    match_results = []
    for _, row in fixtures.iterrows():
        pred = predict_match(row["home_team"], row["away_team"], team_data)
        result = simulate_match_result(pred, knockout=False)
        result["match_id"] = row["match_id"]
        result["group"] = row["group"]
        result["stage"] = "Group Stage"
        result["home_xg"] = pred["home_xg"]
        result["away_xg"] = pred["away_xg"]
        result["top_scores"] = str(pred["top_scores"])
        match_results.append(result)

    df_results = pd.DataFrame(match_results)
    df_tables = _build_group_tables(df_results, groups)
    return df_tables, df_results


def _build_group_tables(df_results: pd.DataFrame, groups: Dict) -> pd.DataFrame:
    """Build standings table for each group."""
    rows = []
    for group, teams in groups.items():
        group_matches = df_results[df_results["group"] == group]

        standings = {t: {"team": t, "group": group, "P": 0, "W": 0, "D": 0, "L": 0,
                         "GF": 0, "GA": 0, "GD": 0, "Pts": 0} for t in teams}

        for _, m in group_matches.iterrows():
            ht, at = m["home_team"], m["away_team"]
            hg, ag = m["home_goals"], m["away_goals"]

            standings[ht]["P"] += 1
            standings[at]["P"] += 1
            standings[ht]["GF"] += hg
            standings[ht]["GA"] += ag
            standings[at]["GF"] += ag
            standings[at]["GA"] += hg

            if hg > ag:
                standings[ht]["W"] += 1
                standings[ht]["Pts"] += 3
                standings[at]["L"] += 1
            elif ag > hg:
                standings[at]["W"] += 1
                standings[at]["Pts"] += 3
                standings[ht]["L"] += 1
            else:
                standings[ht]["D"] += 1
                standings[at]["D"] += 1
                standings[ht]["Pts"] += 1
                standings[at]["Pts"] += 1

        for t in standings.values():
            t["GD"] = t["GF"] - t["GA"]

        group_df = pd.DataFrame(list(standings.values()))
        group_df = group_df.sort_values(["Pts", "GD", "GF"], ascending=False).reset_index(drop=True)
        group_df["position"] = range(1, len(group_df) + 1)
        rows.append(group_df)

    return pd.concat(rows, ignore_index=True)


def get_qualified_teams(df_tables: pd.DataFrame) -> Tuple[Dict, pd.DataFrame]:
    """
    Determine who qualifies:
    - Top 2 from each group → 24 teams
    - Best 8 third-placed teams → 8 more teams
    Total: 32 teams in Round of 32
    """
    top2 = df_tables[df_tables["position"] <= 2].copy()
    third = df_tables[df_tables["position"] == 3].copy()

    # Rank third-placed teams
    third = third.sort_values(["Pts", "GD", "GF"], ascending=False).reset_index(drop=True)
    third["third_rank"] = range(1, len(third) + 1)
    best_third = third[third["third_rank"] <= 8].copy()

    qualified = pd.concat([top2, best_third], ignore_index=True)

    # Build slot → team mapping
    slot_map = {}
    for _, row in top2.iterrows():
        slot = f"{row['position']}{row['group']}"
        slot_map[slot] = row["team"]

    return slot_map, best_third, qualified
