"""
Knockout stage simulation: R32 → R16 → QF → SF → Final.
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.predictor import load_team_data, predict_match, simulate_match_result

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

ROUND_LABELS = {
    "R32": "Round of 32",
    "R16": "Round of 16",
    "QF": "Quarter-Finals",
    "SF": "Semi-Finals",
    "3rd": "Third Place",
    "Final": "Final",
}


def simulate_knockout_stage(
    r32_teams: List[str],
    slot_map: Dict[str, str],
    best_third: pd.DataFrame,
) -> Tuple[pd.DataFrame, str, str]:
    """
    Simulate the entire knockout stage.
    Returns (all_knockout_results_df, winner, runner_up).
    """
    team_data = load_team_data()
    df_bracket = pd.read_csv(DATA_DIR / "reference" / "fixtures_knockout_wc2026.csv")

    all_results = []
    # Track winner of each match by match_id
    match_winners: Dict[str, str] = {}
    match_losers: Dict[str, str] = {}

    # Fill third-place slots with best third-placed teams
    third_slot_map = _assign_third_place(best_third, df_bracket, slot_map)

    def resolve_slot(slot: str) -> Optional[str]:
        slot = str(slot)
        if slot.startswith("W"):
            # Slot is like "W74" → match_id is "M74"
            mid = "M" + slot[1:]
            return match_winners.get(mid)
        elif slot.startswith("RU"):
            # Slot is like "RU101" → match_id is "M101"
            mid = "M" + slot[2:]
            return match_losers.get(mid)
        elif slot in slot_map:
            return slot_map[slot]
        elif slot in third_slot_map:
            return third_slot_map[slot]
        return None

    rounds_order = ["R32", "R16", "QF", "SF", "3rd", "Final"]

    for round_code in rounds_order:
        round_matches = df_bracket[df_bracket["round"] == round_code]

        for _, row in round_matches.iterrows():
            home_team = resolve_slot(row["home_slot"])
            away_team = resolve_slot(row["away_slot"])

            if not home_team or not away_team:
                # Debug: print missing
                import logging
                logging.getLogger(__name__).debug(
                    f"Skip {row['match_id']}: home={row['home_slot']}→{home_team}, away={row['away_slot']}→{away_team}"
                )
                continue

            pred = predict_match(home_team, away_team, team_data, neutral=True)
            result = simulate_match_result(pred, knockout=(round_code != "3rd"))
            result["match_id"] = row["match_id"]
            result["round"] = round_code
            result["round_label"] = ROUND_LABELS.get(round_code, round_code)
            result["stage"] = "Knockout"

            winner = result["winner"]
            loser = away_team if winner == home_team else home_team

            match_winners[row["match_id"]] = winner
            match_losers[row["match_id"]] = loser
            all_results.append(result)

    df_knockout = pd.DataFrame(all_results)
    final = df_knockout[df_knockout["round"] == "Final"]
    if len(final) == 0:
        return df_knockout, "Unknown", "Unknown"

    final_row = final.iloc[0]
    winner = final_row["winner"]
    runner_up = final_row["away_team"] if winner == final_row["home_team"] else final_row["home_team"]

    return df_knockout, winner, runner_up


def _assign_third_place(best_third: pd.DataFrame, df_bracket: pd.DataFrame, slot_map: Dict) -> Dict:
    """
    Map third-place group slots (like '3ABCDF') to actual third-placed teams.
    Each slot encodes which groups are allowed (letters after '3').
    """
    from itertools import permutations

    # Collect unique third-place slots from R32 bracket
    third_slots = []
    r32 = df_bracket[df_bracket["round"] == "R32"]
    for col in ["home_slot", "away_slot"]:
        for val in r32[col].astype(str).unique():
            if val.startswith("3") and val not in third_slots:
                third_slots.append(val)

    teams_info = best_third[["team", "group"]].to_dict("records")

    if len(teams_info) < len(third_slots):
        # Pad with dummy if not enough third-place teams
        teams_info = teams_info[:len(third_slots)]
    elif len(teams_info) > len(third_slots):
        teams_info = teams_info[:len(third_slots)]

    assignment = {}

    # Try all permutations to find valid group assignment
    for perm in permutations(teams_info):
        ok = True
        trial = {}
        for slot, team_row in zip(third_slots, perm):
            # Allowed groups = letters after '3' in slot name
            allowed_groups = list(slot[1:])
            if team_row["group"] not in allowed_groups:
                ok = False
                break
            trial[slot] = team_row["team"]
        if ok:
            assignment = trial
            break

    # Fallback: assign greedily ignoring group constraints
    if not assignment:
        for slot, team_row in zip(third_slots, teams_info):
            assignment[slot] = team_row["team"]

    return assignment
