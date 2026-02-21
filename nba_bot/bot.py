"""
Main NBA betting bot orchestrator.
"""
import csv
import os
from typing import Dict, List, Optional

from nba_bot.probability import (
    moneyline_to_implied_prob,
    decimal_to_implied_prob,
    remove_vig_two_way,
)
from nba_bot.model import NBATeamRatings, NBAModel, normalize_team_name, is_current_nba_team
from nba_bot.betting import calculate_edge, calculate_bet_size
from nba_bot.database import NBADatabase
from nba_bot.config import BANKROLL, MIN_FAVORITE_PROB, MIN_EDGE, NBA_ELO_CSV


class NBABettingBot:
    """Main NBA betting bot orchestrator."""

    def __init__(self, bankroll: float = BANKROLL, db_path: Optional[str] = None):
        self.team_ratings = NBATeamRatings()
        self.model = NBAModel(self.team_ratings)
        self.database = NBADatabase(db_path) if db_path else NBADatabase()
        self.bankroll = bankroll

        # Load persisted team ratings
        saved_ratings = self.database.load_team_ratings()
        if not saved_ratings and NBA_ELO_CSV:
            imported = self._import_ratings_from_csv(NBA_ELO_CSV)
            if imported:
                saved_ratings = self.database.load_team_ratings()
        self.team_ratings.ratings.update(saved_ratings)

    def _import_ratings_from_csv(self, csv_path: str) -> int:
        """Import Elo ratings from a CSV file (team_name/team + elo/rating)."""
        if not os.path.isfile(csv_path):
            print(f"Warning: Elo CSV not found: {csv_path}")
            return 0

        count = 0
        try:
            with open(csv_path, newline='', encoding='utf-8') as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    team = (row.get('team_name') or row.get('team') or '').strip()
                    elo = (row.get('elo') or row.get('rating') or '').strip()
                    if not team or not elo:
                        continue
                    if not is_current_nba_team(team):
                        continue
                    try:
                        elo_val = float(elo)
                    except ValueError:
                        continue
                    self.team_ratings.update_rating(team, elo_val)
                    self.database.save_team_rating(team, elo_val)
                    count += 1
        except Exception as exc:
            print(f"Warning: failed to import Elo CSV: {exc}")
            return 0

        if count:
            print(f"Imported {count} Elo ratings from {csv_path}")
        return count

    # ------------------------------------------------------------------
    # Core analysis
    # ------------------------------------------------------------------

    def analyze_game(
        self,
        home_team: str,
        away_team: str,
        home_ml: Optional[float] = None,
        away_ml: Optional[float] = None,
        home_odds: Optional[float] = None,
        away_odds: Optional[float] = None,
        rest_diff: int = 0,
        home_b2b: bool = False,
        away_b2b: bool = False,
        home_star_out: bool = False,
        away_star_out: bool = False,
        use_calibration: bool = True,
        debug: bool = False,
    ) -> Dict:
        """
        Analyse an NBA game and return a betting recommendation.

        Provide *either* American moneyline odds (home_ml / away_ml) *or*
        decimal odds (home_odds / away_odds) — not both.

        Args:
            home_team: Home team name
            away_team: Away team name
            home_ml: Home moneyline (e.g. -150)
            away_ml: Away moneyline (e.g. +130)
            home_odds: Home decimal odds (alternative to moneyline)
            away_odds: Away decimal odds (alternative to moneyline)
            rest_diff: Extra rest days home team has over away team
            home_b2b: Home team playing back-to-back
            away_b2b: Away team playing back-to-back
            home_star_out: Star player out for home team
            away_star_out: Star player out for away team
            use_calibration: Shrink model probs toward market probs

        Returns:
            Analysis dict with recommendation
        """
        # --- Parse market probabilities ---
        if home_ml is not None and away_ml is not None:
            home_implied = moneyline_to_implied_prob(home_ml)
            away_implied = moneyline_to_implied_prob(away_ml)
            home_bet_odds = _ml_to_decimal(home_ml)
            away_bet_odds = _ml_to_decimal(away_ml)
        elif home_odds is not None and away_odds is not None:
            home_implied = decimal_to_implied_prob(home_odds)
            away_implied = decimal_to_implied_prob(away_odds)
            home_bet_odds = home_odds
            away_bet_odds = away_odds
        else:
            raise ValueError(
                "Provide either (home_ml, away_ml) or (home_odds, away_odds)."
            )

        market_probs = remove_vig_two_way(home_implied, away_implied)

        # --- Model probabilities ---
        true_probs = self.model.predict_win_prob(
            home_team=home_team,
            away_team=away_team,
            rest_diff=rest_diff,
            home_b2b=home_b2b,
            away_b2b=away_b2b,
            home_star_out=home_star_out,
            away_star_out=away_star_out,
            market_probabilities=market_probs if use_calibration else None,
            return_debug=debug,
        )

        debug_info = true_probs.pop('debug', None) if debug else None

        # --- Edges ---
        home_edge = calculate_edge(true_probs['home'], market_probs['home'])
        away_edge = calculate_edge(true_probs['away'], market_probs['away'])

        # --- High hit-rate recommendation ---
        # Only bet the favorite; require model_prob >= MIN_FAVORITE_PROB and edge >= MIN_EDGE
        recommendation = None

        fav_key = 'home' if true_probs['home'] >= true_probs['away'] else 'away'
        fav_prob = true_probs[fav_key]
        fav_market_prob = market_probs[fav_key]
        fav_odds = home_bet_odds if fav_key == 'home' else away_bet_odds
        fav_edge = calculate_edge(fav_prob, fav_market_prob)

        if fav_prob >= MIN_FAVORITE_PROB and fav_edge >= MIN_EDGE:
            bet_size = calculate_bet_size(
                self.bankroll, fav_prob / 100.0, fav_odds, use_flat=True
            )
            recommendation = {
                'bet_type': fav_key,
                'odds': round(fav_odds, 4),
                'stake': round(bet_size, 2),
                'edge': round(fav_edge, 2),
                'true_probability': round(fav_prob, 2),
                'market_probability': round(fav_market_prob, 2),
                'potential_return': round(bet_size * fav_odds, 2),
                'potential_profit': round(bet_size * (fav_odds - 1), 2),
            }

        return {
            'home_team': home_team,
            'away_team': away_team,
            'market_probabilities': {
                'home': round(market_probs['home'], 2),
                'away': round(market_probs['away'], 2),
            },
            'true_probabilities': {
                'home': round(true_probs['home'], 2),
                'away': round(true_probs['away'], 2),
            },
            'edges': {
                'home': round(home_edge, 2),
                'away': round(away_edge, 2),
            },
            'team_ratings': {
                'home': round(self.team_ratings.get_rating(home_team), 0),
                'away': round(self.team_ratings.get_rating(away_team), 0),
            },
            'recommendation': recommendation,
            'calibration_applied': use_calibration,
            'debug': debug_info,
        }

    def analyze_game_manual(
        self,
        home_team: str,
        away_team: str,
        home_odds: float,
        away_odds: float,
    ) -> Dict:
        """
        Thin wrapper around analyze_game() that returns UI-friendly flat keys.

        Returns a dict with:
            home_elo, away_elo,
            market_home, market_away,
            true_home, true_away,
            edge_home, edge_away,
            recommendation (or None) with keys:
                bet_type, odds, stake, true_prob, market_prob, edge
        """
        result = self.analyze_game(
            home_team=home_team,
            away_team=away_team,
            home_odds=home_odds,
            away_odds=away_odds,
        )

        rec = result.get("recommendation")
        ui_rec = None
        if rec:
            ui_rec = {
                "bet_type": rec["bet_type"],
                "odds": rec["odds"],
                "stake": rec["stake"],
                "true_prob": rec["true_probability"],
                "market_prob": rec["market_probability"],
                "edge": rec["edge"],
            }

        return {
            "home_elo": result["team_ratings"]["home"],
            "away_elo": result["team_ratings"]["away"],
            "market_home": result["market_probabilities"]["home"],
            "market_away": result["market_probabilities"]["away"],
            "true_home": result["true_probabilities"]["home"],
            "true_away": result["true_probabilities"]["away"],
            "edge_home": result["edges"]["home"],
            "edge_away": result["edges"]["away"],
            "recommendation": ui_rec,
        }

    # ------------------------------------------------------------------
    # Bet management
    # ------------------------------------------------------------------

    def place_bet(
        self,
        home_team: str,
        away_team: str,
        bet_type: str,
        odds: float,
        stake: float,
        true_probability: float,
        market_probability: float,
        edge: float,
        match_date: Optional[str] = None,
    ) -> int:
        """Record a bet in the database and deduct stake from bankroll."""
        bet_id = self.database.add_bet(
            home_team, away_team, bet_type, odds, stake,
            true_probability, market_probability, edge, match_date,
        )
        self.bankroll -= stake
        return bet_id

    def settle_bet(self, bet_id: int, result: str):
        """
        Settle a bet.

        Args:
            bet_id: Bet ID
            result: 'win', 'loss', or 'push'
        """
        bets = self.database.get_all_bets()
        bet = next((b for b in bets if b['id'] == bet_id), None)

        if not bet:
            print(f"Bet {bet_id} not found")
            return

        if result == 'win':
            profit_loss = bet['stake'] * (bet['odds'] - 1)
            self.bankroll += bet['stake'] + profit_loss
        elif result == 'loss':
            profit_loss = -bet['stake']
        else:  # push
            profit_loss = 0.0
            self.bankroll += bet['stake']

        self.database.update_bet_result(bet_id, result, profit_loss)

    def update_ratings_from_api(self, game_date: str) -> int:
        """
        Fetch final game results from BALLDONTLIE for *game_date* and update Elo.

        Requires BALLDONTLIE_API_KEY in the environment (or .env).

        Args:
            game_date: Date string in YYYY-MM-DD format.

        Returns:
            Number of games processed.
        """
        from nba_bot.api_client import BallDontLieClient
        from nba_bot.elo import update_elo as _update_elo

        client = BallDontLieClient()
        games = client.get_games(game_date)

        updated = 0
        for g in games:
            # Accept "Final", "Final/OT", etc. but not ambiguous substrings.
            # Also check the top-level 'status' field as a fallback.
            period_detail = (g.get("period_detail") or "").lower().strip()
            status = (g.get("status") or "").lower().strip()
            is_final = (
                status == "final"
                or period_detail == "final"
                or period_detail.startswith("final/")
            )
            if not is_final:
                continue

            home_abbr = g["home_team"]["abbreviation"]
            away_abbr = g["visitor_team"]["abbreviation"]
            hs = g.get("home_team_score")
            vs = g.get("visitor_team_score")
            if hs is None or vs is None:
                continue

            home_won = int(hs) > int(vs)

            r_home = self.team_ratings.get_rating(home_abbr)
            r_away = self.team_ratings.get_rating(away_abbr)
            r_home_new, r_away_new = _update_elo(r_home, r_away, home_won)

            self.team_ratings.update_rating(home_abbr, r_home_new)
            self.team_ratings.update_rating(away_abbr, r_away_new)
            self.database.save_team_rating(home_abbr, r_home_new)
            self.database.save_team_rating(away_abbr, r_away_new)
            self.database.add_game_result(
                game_date, home_abbr, away_abbr, int(hs), int(vs)
            )
            updated += 1

        return updated

    # ------------------------------------------------------------------
    # Rating management
    # ------------------------------------------------------------------

    def update_ratings_from_result(
        self,
        home_team: str,
        away_team: str,
        home_score: int,
        away_score: int,
        game_date: Optional[str] = None,
        season: Optional[str] = None,
    ):
        """Update Elo ratings after a game and persist them."""
        home_won = home_score > away_score
        self.team_ratings.update_ratings_after_game(home_team, away_team, home_won)

        self.database.save_team_rating(home_team, self.team_ratings.get_rating(home_team))
        self.database.save_team_rating(away_team, self.team_ratings.get_rating(away_team))

        if game_date:
            self.database.add_game_result(
                game_date, home_team, away_team, home_score, away_score, season
            )

    # ------------------------------------------------------------------
    # Stats / queries
    # ------------------------------------------------------------------

    def get_statistics(self) -> Dict:
        """Return betting statistics including current bankroll."""
        stats = self.database.get_betting_stats()
        stats['current_bankroll'] = round(self.bankroll, 2)
        return stats

    def get_pending_bets(self) -> List[Dict]:
        """Return all unsettled bets."""
        return self.database.get_pending_bets()

    def get_all_bets(self) -> List[Dict]:
        """Return all bets."""
        return self.database.get_all_bets()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ml_to_decimal(ml: float) -> float:
    """Convert American moneyline to decimal odds."""
    if ml > 0:
        return 1.0 + ml / 100.0
    else:
        return 1.0 + 100.0 / abs(ml)
