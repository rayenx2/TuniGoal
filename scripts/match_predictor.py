"""
TuniGoal — Match Outcome Predictor
Tunisian Ligue Professionnelle 1 2024/25 season historical stats.
No ML library required — pure arithmetic weighted scoring.

Usage:
    python scripts/match_predictor.py --demo
    python scripts/match_predictor.py --home "Esperance ST" --away "Club Africain"
"""

import argparse
import json
from typing import TypedDict


class TeamStats(TypedDict):
    home_goals_avg: float
    away_goals_avg: float
    home_win_rate: float
    away_win_rate: float
    head_to_head_wins: int


class PredictionResult(TypedDict):
    outcome: str
    confidence: float
    probabilities: dict
    expected_goals: dict


# Tunisian Ligue Pro 1 2024/25 historical stats
TEAM_STATS: dict[str, TeamStats] = {
    "Esperance ST": {
        "home_goals_avg": 2.8, "away_goals_avg": 2.1,
        "home_win_rate": 0.82, "away_win_rate": 0.68,
        "head_to_head_wins": 8,
    },
    "Club Africain": {
        "home_goals_avg": 2.1, "away_goals_avg": 1.6,
        "home_win_rate": 0.62, "away_win_rate": 0.48,
        "head_to_head_wins": 4,
    },
    "Etoile du Sahel": {
        "home_goals_avg": 2.3, "away_goals_avg": 1.9,
        "home_win_rate": 0.70, "away_win_rate": 0.55,
        "head_to_head_wins": 6,
    },
    "CS Sfaxien": {
        "home_goals_avg": 1.9, "away_goals_avg": 1.5,
        "home_win_rate": 0.60, "away_win_rate": 0.44,
        "head_to_head_wins": 5,
    },
    "US Monastir": {
        "home_goals_avg": 2.0, "away_goals_avg": 1.6,
        "home_win_rate": 0.63, "away_win_rate": 0.47,
        "head_to_head_wins": 4,
    },
    "AS Gabes": {
        "home_goals_avg": 1.5, "away_goals_avg": 1.1,
        "home_win_rate": 0.45, "away_win_rate": 0.30,
        "head_to_head_wins": 2,
    },
    "CA Bizertin": {
        "home_goals_avg": 1.6, "away_goals_avg": 1.2,
        "home_win_rate": 0.48, "away_win_rate": 0.33,
        "head_to_head_wins": 2,
    },
    "CS Hammam-Lif": {
        "home_goals_avg": 1.4, "away_goals_avg": 1.0,
        "home_win_rate": 0.42, "away_win_rate": 0.28,
        "head_to_head_wins": 1,
    },
    "ES Metlaoui": {
        "home_goals_avg": 1.3, "away_goals_avg": 0.9,
        "home_win_rate": 0.38, "away_win_rate": 0.25,
        "head_to_head_wins": 1,
    },
    "AS Marsa": {
        "home_goals_avg": 1.5, "away_goals_avg": 1.1,
        "home_win_rate": 0.44, "away_win_rate": 0.31,
        "head_to_head_wins": 2,
    },
}

WEIGHT_WIN_RATE = 0.50
WEIGHT_GOALS = 0.30
WEIGHT_H2H = 0.12
WEIGHT_HOME_ADVANTAGE = 0.08
MAX_H2H_WINS = 10.0


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def predict_outcome(home_stats: TeamStats, away_stats: TeamStats) -> PredictionResult:
    home_score = (
        home_stats["home_win_rate"] * WEIGHT_WIN_RATE
        + (home_stats["home_goals_avg"] / 5.0) * WEIGHT_GOALS
        + (home_stats["head_to_head_wins"] / MAX_H2H_WINS) * WEIGHT_H2H
        + WEIGHT_HOME_ADVANTAGE
    )
    away_score = (
        away_stats["away_win_rate"] * WEIGHT_WIN_RATE
        + (away_stats["away_goals_avg"] / 5.0) * WEIGHT_GOALS
        + (away_stats["head_to_head_wins"] / MAX_H2H_WINS) * WEIGHT_H2H
    )

    diff = home_score - away_score

    if diff > 0.15:
        home_win = _clamp(0.55 + diff * 0.60, 0.10, 0.80)
        draw = 0.22
        away_win = 1.0 - home_win - draw
    elif diff < -0.10:
        away_win = _clamp(0.50 + abs(diff) * 0.60, 0.10, 0.80)
        draw = 0.22
        home_win = 1.0 - away_win - draw
    else:
        draw = 0.32
        home_win = _clamp(0.38 + diff * 0.50, 0.10, 0.70)
        away_win = 1.0 - home_win - draw

    home_win = _clamp(home_win, 0.05, 0.80)
    away_win = _clamp(away_win, 0.05, 0.80)
    draw = _clamp(draw, 0.10, 0.40)
    total = home_win + draw + away_win
    home_win /= total
    draw /= total
    away_win /= total

    max_prob = max(home_win, draw, away_win)
    if max_prob == home_win:
        outcome = "home_win"
    elif max_prob == away_win:
        outcome = "away_win"
    else:
        outcome = "draw"

    xg_home = round(home_stats["home_goals_avg"] * 0.70 + away_stats["away_goals_avg"] * 0.30 * 0.85, 1)
    xg_away = round(away_stats["away_goals_avg"] * 0.70 + home_stats["home_goals_avg"] * 0.30 * 0.85, 1)

    return PredictionResult(
        outcome=outcome,
        confidence=round(max_prob, 3),
        probabilities={"home_win": round(home_win, 3), "draw": round(draw, 3), "away_win": round(away_win, 3)},
        expected_goals={"home": xg_home, "away": xg_away},
    )


def predict_by_name(home_team: str, away_team: str) -> PredictionResult:
    if home_team not in TEAM_STATS:
        raise ValueError(f"Unknown team: {home_team!r}. Available: {sorted(TEAM_STATS)}")
    if away_team not in TEAM_STATS:
        raise ValueError(f"Unknown team: {away_team!r}. Available: {sorted(TEAM_STATS)}")
    if home_team == away_team:
        raise ValueError("home_team and away_team must be different.")
    return predict_outcome(TEAM_STATS[home_team], TEAM_STATS[away_team])


def _format_result(home: str, away: str, result: PredictionResult) -> str:
    p = result["probabilities"]
    xg = result["expected_goals"]
    lines = [
        f"  Matchup    : {home} vs {away}",
        f"  Outcome    : {result['outcome'].replace('_', ' ').title()}",
        f"  Confidence : {result['confidence'] * 100:.1f}%",
        f"  Probabilities:",
        f"    Home Win : {p['home_win'] * 100:.1f}%",
        f"    Draw     : {p['draw'] * 100:.1f}%",
        f"    Away Win : {p['away_win'] * 100:.1f}%",
        f"  Expected Goals: {home} {xg['home']} — {xg['away']} {away}",
    ]
    return "\n".join(lines)


def demo() -> None:
    fixtures = [
        ("Esperance ST", "Club Africain"),
        ("Etoile du Sahel", "CS Sfaxien"),
        ("US Monastir", "CA Bizertin"),
    ]
    print("\n" + "=" * 60)
    print("  TuniGoal — Match Outcome Predictor")
    print("  Tunisian Ligue Pro 1 2024/25 season stats")
    print("=" * 60)
    for home, away in fixtures:
        result = predict_by_name(home, away)
        print("\n" + _format_result(home, away, result))
        print("-" * 60)
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="TuniGoal — Match Outcome Predictor (Ligue Pro 1)")
    parser.add_argument("--demo", action="store_true", help="Run 3 sample predictions")
    parser.add_argument("--home", type=str, help="Home team name")
    parser.add_argument("--away", type=str, help="Away team name")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.demo:
        demo()
        return

    if args.home and args.away:
        result = predict_by_name(args.home, args.away)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("\n" + _format_result(args.home, args.away, result))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
