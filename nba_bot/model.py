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


CURRENT_NBA_TEAMS = {
    'Atlanta Hawks', 'Boston Celtics', 'Brooklyn Nets', 'Charlotte Hornets',
    'Chicago Bulls', 'Cleveland Cavaliers', 'Dallas Mavericks', 'Denver Nuggets',
    'Detroit Pistons', 'Golden State Warriors', 'Houston Rockets', 'Indiana Pacers',
    'Los Angeles Clippers', 'Los Angeles Lakers', 'Memphis Grizzlies', 'Miami Heat',
    'Milwaukee Bucks', 'Minnesota Timberwolves', 'New Orleans Pelicans',
    'New York Knicks', 'Oklahoma City Thunder', 'Orlando Magic',
    'Philadelphia 76ers', 'Phoenix Suns', 'Portland Trail Blazers',
    'Sacramento Kings', 'San Antonio Spurs', 'Toronto Raptors',
    'Utah Jazz', 'Washington Wizards',
}


def normalize_team_name(name: str) -> str:
    """Normalize common NBA team name variations to a canonical form."""
    if not name:
        return ""
    n = " ".join(str(name).strip().split())
    aliases = {
        # Common name variants
        'la lakers': 'Los Angeles Lakers',
        'la clippers': 'Los Angeles Clippers',
        'gs warriors': 'Golden State Warriors',
        'ny knicks': 'New York Knicks',
        'no pelicans': 'New Orleans Pelicans',
        'new orleans': 'New Orleans Pelicans',
        'new orleans pelicans': 'New Orleans Pelicans',
        'pelicans': 'New Orleans Pelicans',
        'nola': 'New Orleans Pelicans',
        '76ers': 'Philadelphia 76ers',
        'sixers': 'Philadelphia 76ers',
        'philadelphia': 'Philadelphia 76ers',
        'philadelphia 76ers': 'Philadelphia 76ers',
        'spurs': 'San Antonio Spurs',
        'lakers': 'Los Angeles Lakers',
        'clippers': 'Los Angeles Clippers',
        'warriors': 'Golden State Warriors',
        'thunder': 'Oklahoma City Thunder',
        'knicks': 'New York Knicks',
        'suns': 'Phoenix Suns',
        'blazers': 'Portland Trail Blazers',
        'trail blazers': 'Portland Trail Blazers',
        'wolves': 'Minnesota Timberwolves',
        'timberwolves': 'Minnesota Timberwolves',
        'cavs': 'Cleveland Cavaliers',
        'mavs': 'Dallas Mavericks',

        # Team abbreviations
        'atl': 'Atlanta Hawks',
        'bos': 'Boston Celtics',
        'brk': 'Brooklyn Nets',
        'bkn': 'Brooklyn Nets',
        'chi': 'Chicago Bulls',
        'cho': 'Charlotte Hornets',
        'cha': 'Charlotte Hornets',
        'cle': 'Cleveland Cavaliers',
        'dal': 'Dallas Mavericks',
        'den': 'Denver Nuggets',
        'det': 'Detroit Pistons',
        'gsw': 'Golden State Warriors',
        'hou': 'Houston Rockets',
        'ind': 'Indiana Pacers',
        'lac': 'Los Angeles Clippers',
        'lal': 'Los Angeles Lakers',
        'mem': 'Memphis Grizzlies',
        'mia': 'Miami Heat',
        'mil': 'Milwaukee Bucks',
        'min': 'Minnesota Timberwolves',
        'nop': 'New Orleans Pelicans',
        'no': 'New Orleans Pelicans',
        'nor': 'New Orleans Pelicans',
        'nyk': 'New York Knicks',
        'okc': 'Oklahoma City Thunder',
        'orl': 'Orlando Magic',
        'phi': 'Philadelphia 76ers',
        'pho': 'Phoenix Suns',
        'phx': 'Phoenix Suns',
        'por': 'Portland Trail Blazers',
        'sac': 'Sacramento Kings',
        'sas': 'San Antonio Spurs',
        'tor': 'Toronto Raptors',
        'uta': 'Utah Jazz',
        'was': 'Washington Wizards',
    }
    canonical = aliases.get(n.lower())
    if canonical:
        return canonical
    return n


def is_current_nba_team(name: str) -> bool:
    """Return True if the provided team name maps to a current NBA franchise."""
    return normalize_team_name(name) in CURRENT_NBA_TEAMS


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

    def _compute_adjusted_ratings(
        self,
        home_team: str,
        away_team: str,
        rest_diff: int = 0,
        home_b2b: bool = False,
        away_b2b: bool = False,
        home_star_out: bool = False,
        away_star_out: bool = False,
    ) -> Dict[str, float]:
        """Compute adjusted Elo values and raw home win probability."""
        home_rating = self.team_ratings.get_rating(home_team)
        away_rating = self.team_ratings.get_rating(away_team)

        adj_home = home_rating + self.home_court_elo
        adj_home += rest_diff * self.rest_elo_per_day

        if home_b2b:
            adj_home -= self.b2b_penalty_elo

        adj_away = away_rating
        if away_b2b:
            adj_away -= self.b2b_penalty_elo

        if home_star_out:
            adj_home -= self.star_out_penalty_elo
        if away_star_out:
            adj_away -= self.star_out_penalty_elo

        home_win_p = self.team_ratings.expected_score(adj_home, adj_away)

        return {
            'home_rating': home_rating,
            'away_rating': away_rating,
            'adj_home_rating': adj_home,
            'adj_away_rating': adj_away,
            'elo_diff': adj_home - adj_away,
            'home_win_p_raw': home_win_p,
        }

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
        return_debug: bool = False,
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
        adjusted = self._compute_adjusted_ratings(
            home_team=home_team,
            away_team=away_team,
            rest_diff=rest_diff,
            home_b2b=home_b2b,
            away_b2b=away_b2b,
            home_star_out=home_star_out,
            away_star_out=away_star_out,
        )

        home_win_p = adjusted['home_win_p_raw']

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
            result = {
                'home': (calibrated['home'] / cal_total) * 100.0,
                'away': (calibrated['away'] / cal_total) * 100.0,
            }
            if return_debug:
                result['debug'] = adjusted
            return result

        if return_debug:
            raw_probs['debug'] = adjusted

        return raw_probs
