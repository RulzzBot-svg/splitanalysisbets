"""
NBA team rating and prediction model using Elo ratings.

Key differences from soccer:
- 2-way outcomes only (home win / away win — no draw)
- Home court advantage expressed in Elo points (default +50)
- Rest differential adjustment (+15 Elo per extra rest day)
- Back-to-back penalty (-30 Elo for the team on B2B)
- Optional star-out injury toggle (manual, -50 Elo per flagged team)
"""
import math
from typing import Dict, Optional
from nba_bot.config import (
    HOME_COURT_ELO, ELO_K_FACTOR, INITIAL_ELO,
    REST_ELO_PER_DAY, B2B_PENALTY_ELO, STAR_OUT_PENALTY_ELO,
    MARKET_SHRINK_FACTOR, MIN_PROBABILITY, MAX_PROBABILITY,
)


def normalize_team_name(name: str) -> str:
    """Normalize common NBA team name variations to a canonical form."""
    if not name:
        return ""
    n = " ".join(str(name).strip().split())
    aliases = {
        'la lakers': 'Los Angeles Lakers',
        'la clippers': 'Los Angeles Clippers',
        'gs warriors': 'Golden State Warriors',
        'gsw': 'Golden State Warriors',
        'lal': 'Los Angeles Lakers',
        'lac': 'Los Angeles Clippers',
        'bkn': 'Brooklyn Nets',
        'ny knicks': 'New York Knicks',
        'nyk': 'New York Knicks',
        'sa spurs': 'San Antonio Spurs',
        'sas': 'San Antonio Spurs',
        'okc': 'Oklahoma City Thunder',
        'no pelicans': 'New Orleans Pelicans',
        'nop': 'New Orleans Pelicans',
    }
    canonical = aliases.get(n.lower())
    if canonical:
        return canonical
    return n


class NBATeamRatings:
    """Manage NBA team Elo ratings."""

    def __init__(self):
        self.ratings: Dict[str, float] = {}
        self.k_factor: int = ELO_K_FACTOR
        self.initial_rating: int = INITIAL_ELO

    def get_rating(self, team_name: str) -> float:
        """Return team Elo rating, initialising to default if new."""
        key = normalize_team_name(team_name)
        if key not in self.ratings:
            self.ratings[key] = float(self.initial_rating)
        return self.ratings[key]

    def update_rating(self, team_name: str, new_rating: float):
        """Directly set a team's Elo rating."""
        key = normalize_team_name(team_name)
        self.ratings[key] = new_rating

    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """
        Standard Elo expected score for team A against team B.

        Returns:
            Expected score in [0, 1]
        """
        return 1.0 / (1.0 + math.pow(10.0, (rating_b - rating_a) / 400.0))

    def update_ratings_after_game(self, home_team: str, away_team: str,
                                  home_won: bool):
        """
        Update Elo ratings after an NBA game (binary result — no draws).

        Args:
            home_team: Home team name
            away_team: Away team name
            home_won: True if home team won
        """
        home_key = normalize_team_name(home_team)
        away_key = normalize_team_name(away_team)

        home_rating = self.get_rating(home_key)
        away_rating = self.get_rating(away_key)

        home_expected = self.expected_score(home_rating, away_rating)
        away_expected = 1.0 - home_expected

        home_actual = 1.0 if home_won else 0.0
        away_actual = 0.0 if home_won else 1.0

        self.update_rating(home_key, home_rating + self.k_factor * (home_actual - home_expected))
        self.update_rating(away_key, away_rating + self.k_factor * (away_actual - away_expected))


class NBAModel:
    """Predict NBA game win probabilities using adjusted Elo."""

    def __init__(self, team_ratings: NBATeamRatings):
        self.team_ratings = team_ratings
        self.home_court_elo = HOME_COURT_ELO
        self.rest_elo_per_day = REST_ELO_PER_DAY
        self.b2b_penalty_elo = B2B_PENALTY_ELO
        self.star_out_penalty_elo = STAR_OUT_PENALTY_ELO
        self.market_shrink_factor = MARKET_SHRINK_FACTOR

    def predict_win_prob(
        self,
        home_team: str,
        away_team: str,
        rest_diff: int = 0,
        home_b2b: bool = False,
        away_b2b: bool = False,
        home_star_out: bool = False,
        away_star_out: bool = False,
        market_probabilities: Optional[Dict[str, float]] = None,
    ) -> Dict[str, float]:
        """
        Predict 2-way win probabilities for a NBA game.

        Args:
            home_team: Home team name
            away_team: Away team name
            rest_diff: Extra rest days home team has over away team
                       (positive = home has more rest, negative = away has more)
            home_b2b: True if home team is on a back-to-back
            away_b2b: True if away team is on a back-to-back
            home_star_out: True if home team has a star player out
            away_star_out: True if away team has a star player out
            market_probabilities: Optional {'home': %, 'away': %} for calibration

        Returns:
            Dictionary with 'home' and 'away' win probabilities (as percentages)
        """
        home_rating = self.team_ratings.get_rating(home_team)
        away_rating = self.team_ratings.get_rating(away_team)

        # 1. Home court advantage
        adj_home = home_rating + self.home_court_elo

        # 2. Rest differential (positive rest_diff benefits home team)
        adj_home += rest_diff * self.rest_elo_per_day

        # 3. Back-to-back penalties
        if home_b2b:
            adj_home -= self.b2b_penalty_elo
        adj_away = away_rating
        if away_b2b:
            adj_away -= self.b2b_penalty_elo

        # 4. Star-out injuries
        if home_star_out:
            adj_home -= self.star_out_penalty_elo
        if away_star_out:
            adj_away -= self.star_out_penalty_elo

        # 5. 2-way win probability via logistic Elo formula
        home_win_p = self.team_ratings.expected_score(adj_home, adj_away)  # [0, 1]

        # Convert to percentages, clamp to safe range
        home_prob = max(MIN_PROBABILITY, min(MAX_PROBABILITY, home_win_p * 100.0))
        away_prob = max(MIN_PROBABILITY, min(MAX_PROBABILITY, (1.0 - home_win_p) * 100.0))

        # Re-normalise after clamping so they sum to 100
        total = home_prob + away_prob
        home_prob = (home_prob / total) * 100.0
        away_prob = (away_prob / total) * 100.0

        raw_probs = {'home': home_prob, 'away': away_prob}

        # 6. Optional market calibration (shrink toward market)
        if market_probabilities and self.market_shrink_factor > 0:
            calibrated = {}
            for side in ('home', 'away'):
                model_p = raw_probs[side]
                market_p = market_probabilities.get(side, model_p)
                calibrated[side] = (
                    (1.0 - self.market_shrink_factor) * model_p
                    + self.market_shrink_factor * market_p
                )
            # Re-normalise after calibration
            cal_total = calibrated['home'] + calibrated['away']
            return {
                'home': (calibrated['home'] / cal_total) * 100.0,
                'away': (calibrated['away'] / cal_total) * 100.0,
            }

        return raw_probs
