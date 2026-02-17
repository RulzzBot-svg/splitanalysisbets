"""
Main application for soccer betting bot
"""
from typing import Dict, Optional, List
try:
    from soccer_bot.api_client import FootballDataClient
except Exception:
    FootballDataClient = None
from soccer_bot.probability import odds_to_implied_probability, remove_bookmaker_margin
from soccer_bot.model import TeamRatings, PredictionModel
from soccer_bot.betting import calculate_edge, should_bet, calculate_bet_size
from soccer_bot.database import BettingDatabase
from soccer_bot.config import BANKROLL, EDGE_THRESHOLD


class SoccerBettingBot:
    """Main betting bot orchestrator"""
    
    def __init__(self, api_key: Optional[str] = None, bankroll: float = BANKROLL):
        self.api_client = FootballDataClient(api_key) if api_key else None
        self.team_ratings = TeamRatings()
        self.prediction_model = PredictionModel(self.team_ratings)
        self.database = BettingDatabase()
        self.bankroll = bankroll
        
        # Load existing team ratings from database
        saved_ratings = self.database.load_team_ratings()
        self.team_ratings.ratings.update(saved_ratings)
    
    def analyze_match_manual(self, home_team: str, away_team: str,
                           home_odds: float, draw_odds: float, away_odds: float,
                           home_form: float = 0.0, away_form: float = 0.0,
                           home_goal_diff: int = 0, away_goal_diff: int = 0,
                           use_calibration: bool = True) -> Dict:
        """
        Analyze a match with manual odds input
        
        Args:
            home_team: Home team name
            away_team: Away team name
            home_odds: Decimal odds for home win
            draw_odds: Decimal odds for draw
            away_odds: Decimal odds for away win
            home_form: Recent form for home team (-1 to 1)
            away_form: Recent form for away team (-1 to 1)
            home_goal_diff: Goal difference for home team
            away_goal_diff: Goal difference for away team
            use_calibration: Apply market calibration to model probabilities
            
        Returns:
            Analysis dictionary with recommendations
        """
        # Convert odds to implied probabilities
        home_implied = odds_to_implied_probability(home_odds)
        draw_implied = odds_to_implied_probability(draw_odds)
        away_implied = odds_to_implied_probability(away_odds)
        
        # Remove bookmaker margin
        market_probs = remove_bookmaker_margin(home_implied, draw_implied, away_implied)
        
        # Get true probabilities from model (with optional market calibration)
        true_probs = self.prediction_model.predict_match_probabilities(
            home_team, away_team, home_form, away_form, home_goal_diff, away_goal_diff,
            market_probabilities=market_probs if use_calibration else None
        )
        
        # Calculate edges
        home_edge = calculate_edge(true_probs['home'], market_probs['home'])
        draw_edge = calculate_edge(true_probs['draw'], market_probs['draw'])
        away_edge = calculate_edge(true_probs['away'], market_probs['away'])
        
        # Determine best bet
        edges = [
            ('home', home_edge, home_odds, true_probs['home'], market_probs['home']),
            ('draw', draw_edge, draw_odds, true_probs['draw'], market_probs['draw']),
            ('away', away_edge, away_odds, true_probs['away'], market_probs['away'])
        ]
        
        best_bet = max(edges, key=lambda x: x[1])
        bet_type, edge, odds, true_prob, market_prob = best_bet
        
        recommendation = None
        if should_bet(edge, EDGE_THRESHOLD):
            # Calculate bet size using improved Kelly or flat staking
            bet_size = calculate_bet_size(self.bankroll, true_prob / 100.0, odds)
            
            recommendation = {
                'bet_type': bet_type,
                'odds': odds,
                'stake': round(bet_size, 2),
                'edge': round(edge, 2),
                'true_probability': round(true_prob, 2),
                'market_probability': round(market_prob, 2),
                'potential_return': round(bet_size * odds, 2),
                'potential_profit': round(bet_size * (odds - 1), 2)
            }
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'market_probabilities': {
                'home': round(market_probs['home'], 2),
                'draw': round(market_probs['draw'], 2),
                'away': round(market_probs['away'], 2)
            },
            'true_probabilities': {
                'home': round(true_probs['home'], 2),
                'draw': round(true_probs['draw'], 2),
                'away': round(true_probs['away'], 2)
            },
            'edges': {
                'home': round(home_edge, 2),
                'draw': round(draw_edge, 2),
                'away': round(away_edge, 2)
            },
            'team_ratings': {
                'home': round(self.team_ratings.get_rating(home_team), 0),
                'away': round(self.team_ratings.get_rating(away_team), 0)
            },
            'recommendation': recommendation,
            'calibration_applied': use_calibration
        }
    
    def place_bet(self, home_team: str, away_team: str, bet_type: str,
                  odds: float, stake: float, true_probability: float,
                  market_probability: float, edge: float,
                  match_date: Optional[str] = None) -> int:
        """
        Place a bet and record it in the database
        
        Args:
            home_team: Home team name
            away_team: Away team name
            bet_type: Type of bet ('home', 'draw', 'away')
            odds: Decimal odds
            stake: Bet amount
            true_probability: Estimated true probability (%)
            market_probability: Market implied probability (%)
            edge: Calculated edge (%)
            match_date: Optional match date
            
        Returns:
            Bet ID
        """
        bet_id = self.database.add_bet(
            home_team, away_team, bet_type, odds, stake,
            true_probability, market_probability, edge, match_date
        )
        
        # Update bankroll
        self.bankroll -= stake
        
        return bet_id
    
    def settle_bet(self, bet_id: int, result: str):
        """
        Settle a bet with result
        
        Args:
            bet_id: Bet ID
            result: Result ('win', 'loss', 'push')
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
    
    def update_ratings_from_result(self, home_team: str, away_team: str,
                                   home_score: int, away_score: int,
                                   match_date: Optional[str] = None):
        """
        Update team ratings based on match result
        
        Args:
            home_team: Home team name
            away_team: Away team name
            home_score: Goals scored by home team
            away_score: Goals scored by away team
            match_date: Optional match date
        """
        self.team_ratings.update_ratings_after_match(
            home_team, away_team, home_score, away_score
        )
        
        # Save updated ratings
        self.database.save_team_rating(home_team, self.team_ratings.get_rating(home_team))
        self.database.save_team_rating(away_team, self.team_ratings.get_rating(away_team))
        
        # Save match result
        if match_date:
            self.database.add_match_result(
                match_date, home_team, away_team, home_score, away_score
            )
    
    def get_statistics(self) -> Dict:
        """Get betting statistics"""
        stats = self.database.get_betting_stats()
        stats['current_bankroll'] = round(self.bankroll, 2)
        return stats
    
    def get_pending_bets(self) -> List[Dict]:
        """Get pending bets"""
        return self.database.get_pending_bets()
    
    def get_all_bets(self) -> List[Dict]:
        """Get all bets"""
        return self.database.get_all_bets()
