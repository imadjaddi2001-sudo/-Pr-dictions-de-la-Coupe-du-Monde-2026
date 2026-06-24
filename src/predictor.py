"""
Match predictor using ELO-based win probability.
Simulates group stage, R32, R16, QF, SF, Final.
"""
import math, random
import numpy as np
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# ELO data from pre-computed project
ELO_RATINGS = {
    "Spain":2229.76,"Argentina":2179.65,"France":2124.78,"England":2094.72,
    "Brazil":2050.19,"Colombia":2064.03,"Netherlands":2019.42,"Germany":1987.74,
    "Ecuador":2015.36,"Portugal":2023.47,"Croatia":1994.76,"Morocco":1972.94,
    "Uruguay":1976.01,"Norway":1964.61,"Japan":1963.04,"Mexico":1959.69,
    "Turkey":1936.92,"Switzerland":1942.83,"Canada":1896.29,"Paraguay":1919.33,
    "South Korea":1877.97,"Senegal":1926.79,"United States":1832.95,"Belgium":1923.02,
    "Australia":1883.42,"Panama":1849.74,"Algeria":1850.76,"Austria":1872.87,
    "Jordan":1780.65,"New Zealand":1766.96,"Iran":1872.96,"Scotland":1830.64,
    "DR Congo":1750.40,"Bosnia and Herzegovina":1632.96,"Cape Verde":1657.00,
    "Tunisia":1734.55,"Curaçao":1621.16,"Sweden":1754.88,"Czech Republic":1773.84,
    "Egypt":1801.42,"South Africa":1666.81,"Ivory Coast":1784.24,"Saudi Arabia":1687.32,
    "Qatar":1591.44,"Ghana":1615.83,"Haiti":1692.28,"Iraq":1710.78,"Uzbekistan":1823.33,
}

GROUPS = {
    "A": ["Mexico","South Africa","South Korea","Czech Republic"],
    "B": ["Canada","Bosnia and Herzegovina","Qatar","Switzerland"],
    "C": ["Brazil","Morocco","Haiti","Scotland"],
    "D": ["United States","Paraguay","Australia","Turkey"],
    "E": ["Germany","Curaçao","Ivory Coast","Ecuador"],
    "F": ["Netherlands","Japan","Sweden","Tunisia"],
    "G": ["Belgium","Egypt","Iran","New Zealand"],
    "H": ["Spain","Cape Verde","Saudi Arabia","Uruguay"],
    "I": ["France","Senegal","Iraq","Norway"],
    "J": ["Argentina","Algeria","Austria","Jordan"],
    "K": ["Portugal","DR Congo","Uzbekistan","Colombia"],
    "L": ["England","Croatia","Ghana","Panama"],
}

CONF_FLAGS = {
    "UEFA":"🇪🇺","CONMEBOL":"🌎","CAF":"🌍","AFC":"🌏","CONCACAF":"🌐","OFC":"🏝️"
}

CONFEDERATIONS = {
    "Spain":"UEFA","Argentina":"CONMEBOL","France":"UEFA","England":"UEFA",
    "Portugal":"UEFA","Brazil":"CONMEBOL","Netherlands":"UEFA","Morocco":"CAF",
    "Belgium":"UEFA","Germany":"UEFA","Croatia":"UEFA","Colombia":"CONMEBOL",
    "Senegal":"CAF","Mexico":"CONCACAF","United States":"CONCACAF","Uruguay":"CONMEBOL",
    "Japan":"AFC","Switzerland":"UEFA","Iran":"AFC","Turkey":"UEFA","Ecuador":"CONMEBOL",
    "Austria":"UEFA","South Korea":"AFC","Australia":"AFC","Algeria":"CAF","Egypt":"CAF",
    "Canada":"CONCACAF","Norway":"UEFA","Panama":"CONCACAF","Ivory Coast":"CAF",
    "Sweden":"UEFA","Paraguay":"CONMEBOL","Czech Republic":"UEFA","Scotland":"UEFA",
    "Tunisia":"CAF","DR Congo":"CAF","Uzbekistan":"AFC","Qatar":"AFC","Iraq":"AFC",
    "South Africa":"CAF","Saudi Arabia":"AFC","Jordan":"AFC","Bosnia and Herzegovina":"UEFA",
    "Cape Verde":"CAF","Ghana":"CAF","Curaçao":"CONCACAF","Haiti":"CONCACAF","New Zealand":"OFC",
}

FIFA_RANKS = {
    "France":1,"Spain":2,"Argentina":3,"England":4,"Portugal":5,"Brazil":6,
    "Netherlands":7,"Morocco":8,"Belgium":9,"Germany":10,"Croatia":11,
    "Colombia":13,"Senegal":14,"Mexico":15,"United States":16,"Uruguay":17,
    "Japan":18,"Switzerland":19,"Iran":21,"Turkey":22,"Ecuador":23,"Austria":24,
    "South Korea":25,"Australia":27,"Algeria":28,"Egypt":29,"Canada":30,"Norway":31,
    "Panama":33,"Ivory Coast":34,"Sweden":38,"Paraguay":40,"Czech Republic":41,
    "Scotland":43,"Tunisia":44,"DR Congo":46,"Uzbekistan":50,"Qatar":55,"Iraq":57,
    "South Africa":60,"Saudi Arabia":61,"Jordan":63,"Bosnia and Herzegovina":65,
    "Cape Verde":69,"Ghana":74,"Curaçao":82,"Haiti":83,"New Zealand":85,
}


def elo_win_prob(elo_home: float, elo_away: float, neutral: bool = True) -> tuple:
    """Return (p_home_win, p_draw, p_away_win) using ELO."""
    home_adv = 0 if neutral else 65
    diff = (elo_home + home_adv) - elo_away
    p_home = 1 / (1 + 10 ** (-diff / 400))
    p_away = 1 - p_home
    # Estimate draw probability using a logistic-like model
    draw_factor = max(0.05, 0.32 - abs(diff) / 3000)
    p_home_adj = p_home * (1 - draw_factor)
    p_away_adj = p_away * (1 - draw_factor)
    return round(p_home_adj, 4), round(draw_factor, 4), round(p_away_adj, 4)


def simulate_match(team_a: str, team_b: str, neutral: bool = True) -> dict:
    """Simulate a single match and return result with probabilities."""
    elo_a = ELO_RATINGS.get(team_a, 1500)
    elo_b = ELO_RATINGS.get(team_b, 1500)
    p_win, p_draw, p_loss = elo_win_prob(elo_a, elo_b, neutral)
    r = random.random()
    if r < p_win:
        winner, outcome = team_a, "home_win"
        score_a = random.randint(1, 4)
        score_b = random.randint(0, score_a - 1)
    elif r < p_win + p_draw:
        winner, outcome = None, "draw"
        g = random.randint(0, 3)
        score_a = score_b = g
    else:
        winner, outcome = team_b, "away_win"
        score_b = random.randint(1, 4)
        score_a = random.randint(0, score_b - 1)
    return {
        "team_a": team_a, "team_b": team_b,
        "score_a": score_a, "score_b": score_b,
        "winner": winner, "outcome": outcome,
        "p_a_win": p_win, "p_draw": p_draw, "p_b_win": p_loss,
    }


def simulate_group(group: str, teams: list) -> pd.DataFrame:
    """Simulate all matches in a group. Returns standings DataFrame."""
    standings = {t: {"team": t, "group": group, "pts": 0, "gf": 0, "ga": 0, "gd": 0, "w": 0, "d": 0, "l": 0} for t in teams}
    matches = []
    for i in range(len(teams)):
        for j in range(i + 1, len(teams)):
            m = simulate_match(teams[i], teams[j], neutral=True)
            matches.append(m)
            # Update standings
            standings[teams[i]]["gf"] += m["score_a"]
            standings[teams[i]]["ga"] += m["score_b"]
            standings[teams[j]]["gf"] += m["score_b"]
            standings[teams[j]]["ga"] += m["score_a"]
            standings[teams[i]]["gd"] = standings[teams[i]]["gf"] - standings[teams[i]]["ga"]
            standings[teams[j]]["gd"] = standings[teams[j]]["gf"] - standings[teams[j]]["ga"]
            if m["outcome"] == "home_win":
                standings[teams[i]]["pts"] += 3
                standings[teams[i]]["w"] += 1
                standings[teams[j]]["l"] += 1
            elif m["outcome"] == "draw":
                standings[teams[i]]["pts"] += 1
                standings[teams[j]]["pts"] += 1
                standings[teams[i]]["d"] += 1
                standings[teams[j]]["d"] += 1
            else:
                standings[teams[j]]["pts"] += 3
                standings[teams[j]]["w"] += 1
                standings[teams[i]]["l"] += 1

    df = pd.DataFrame(list(standings.values()))
    df = df.sort_values(["pts", "gd", "gf"], ascending=False).reset_index(drop=True)
    df["position"] = range(1, len(df) + 1)
    return df, matches


def get_best_thirds(all_groups_standings: dict) -> list:
    """Pick best 8 third-placed teams from 12 groups (R32 has 16 slots from thirds)."""
    thirds = []
    for grp, df in all_groups_standings.items():
        third_row = df[df["position"] == 3].iloc[0].to_dict()
        third_row["group"] = grp
        thirds.append(third_row)
    thirds.sort(key=lambda x: (x["pts"], x["gd"], x["gf"]), reverse=True)
    return thirds[:8]


def simulate_knockout_match(team_a: str, team_b: str) -> str:
    """Knockout: no draws — ET/penalties decide."""
    m = simulate_match(team_a, team_b, neutral=True)
    if m["winner"] is None:
        # Penalties: 50/50 with slight ELO tilt
        elo_a = ELO_RATINGS.get(team_a, 1500)
        elo_b = ELO_RATINGS.get(team_b, 1500)
        p = 0.5 + (elo_a - elo_b) / 8000
        return team_a if random.random() < p else team_b
    return m["winner"]


def run_full_tournament(n_sim: int = 1000) -> dict:
    """
    Monte Carlo simulation of full WC 2026 tournament.
    Returns probabilities for each stage for each team.
    """
    stage_counts = {team: {"R32": 0, "R16": 0, "QF": 0, "SF": 0, "Final": 0, "Winner": 0}
                    for team in ELO_RATINGS}

    for _ in range(n_sim):
        result = _simulate_once()
        for stage, teams in result.items():
            for t in teams:
                if t in stage_counts:
                    stage_counts[t][stage] += 1

    probs = {}
    for team, counts in stage_counts.items():
        probs[team] = {stage: round(cnt / n_sim, 4) for stage, cnt in counts.items()}
    return probs


def _simulate_once() -> dict:
    """Single tournament simulation. Returns dict of {stage: [teams]}."""
    # Group stage
    all_standings = {}
    direct_qualifiers = {}  # {slot: team}  e.g. "1A": "Mexico"

    for grp, teams in GROUPS.items():
        df_grp, _ = simulate_group(grp, teams)
        all_standings[grp] = df_grp
        direct_qualifiers[f"1{grp}"] = df_grp[df_grp["position"] == 1].iloc[0]["team"]
        direct_qualifiers[f"2{grp}"] = df_grp[df_grp["position"] == 2].iloc[0]["team"]

    best_thirds = get_best_thirds(all_standings)
    r32_teams = list(direct_qualifiers.values()) + [t["team"] for t in best_thirds]

    # Round of 32 (16 matches)
    r16_teams = _play_round(r32_teams)
    qf_teams = _play_round(r16_teams)
    sf_teams = _play_round(qf_teams)
    final_teams = _play_round(sf_teams)
    winner_list = _play_round(final_teams)

    return {
        "R32": r32_teams,
        "R16": r16_teams,
        "QF": qf_teams,
        "SF": sf_teams,
        "Final": final_teams,
        "Winner": winner_list,
    }


def _play_round(teams: list) -> list:
    """Play a knockout round. Pair teams sequentially."""
    winners = []
    for i in range(0, len(teams), 2):
        if i + 1 < len(teams):
            w = simulate_knockout_match(teams[i], teams[i + 1])
            winners.append(w)
        else:
            winners.append(teams[i])  # bye
    return winners


def predict_match_head2head(team_a: str, team_b: str) -> dict:
    """Return head-to-head prediction stats for two teams."""
    elo_a = ELO_RATINGS.get(team_a, 1500)
    elo_b = ELO_RATINGS.get(team_b, 1500)
    p_win, p_draw, p_loss = elo_win_prob(elo_a, elo_b)
    return {
        "team_a": team_a,
        "team_b": team_b,
        "elo_a": elo_a,
        "elo_b": elo_b,
        "rank_a": FIFA_RANKS.get(team_a, 99),
        "rank_b": FIFA_RANKS.get(team_b, 99),
        "conf_a": CONFEDERATIONS.get(team_a, ""),
        "conf_b": CONFEDERATIONS.get(team_b, ""),
        "p_a_win": p_win,
        "p_draw": p_draw,
        "p_b_win": p_loss,
        "favorite": team_a if p_win > p_loss else team_b,
        "margin": abs(p_win - p_loss),
    }
