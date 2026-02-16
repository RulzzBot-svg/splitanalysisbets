"""
Team rating and prediction model using Elo ratings
"""
import math
from typing import Dict, Tuple
from soccer_bot.config import HOME_ADVANTAGE_ELO, ELO_K_FACTOR, INITIAL_ELO, MARKET_SHRINK_FACTOR, MIN_PROBABILITY, MAX_PROBABILITY


class TeamRatings:
    """Manage team Elo ratings"""
    
    def __init__(self):
        self.ratings: Dict[str, float] = {}
        self.k_factor = ELO_K_FACTOR
        self.initial_rating = INITIAL_ELO
    
    def get_rating(self, team_name: str) -> float:
        """Get team's Elo rating, initialize if new team"""
        if team_name not in self.ratings:
            self.ratings[team_name] = self.initial_rating
        return self.ratings[team_name]
    
    def update_rating(self, team_name: str, new_rating: float):
        """Update team's Elo rating"""
        self.ratings[team_name] = new_rating
    
    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """
        Calculate expected score for team A against team B
        
        Args:
            rating_a: Elo rating of team A
            rating_b: Elo rating of team B
            
        Returns:
            Expected score (0-1)
        """
        return 1.0 / (1.0 + math.pow(10, (rating_b - rating_a) / 400.0))
    
    def update_ratings_after_match(self, home_team: str, away_team: str, 
                                   home_score: int, away_score: int):
        """
        Update Elo ratings after a match
        
        Args:
            home_team: Home team name
            away_team: Away team name
            home_score: Goals scored by home team
            away_score: Goals scored by away team
        """
        home_rating = self.get_rating(home_team)
        away_rating = self.get_rating(away_team)
        
        # Calculate expected scores
        home_expected = self.expected_score(home_rating, away_rating)
        away_expected = 1.0 - home_expected
        
        # Determine actual scores (1 for win, 0.5 for draw, 0 for loss)
        if home_score > away_score:
            home_actual, away_actual = 1.0, 0.0
        elif home_score < away_score:
            home_actual, away_actual = 0.0, 1.0
        else:
            home_actual, away_actual = 0.5, 0.5
        
        # Update ratings
        new_home_rating = home_rating + self.k_factor * (home_actual - home_expected)
        new_away_rating = away_rating + self.k_factor * (away_actual - away_expected)
        
        self.update_rating(home_team, new_home_rating)
        self.update_rating(away_team, new_away_rating)


class PredictionModel:
    """Predict match outcomes using Elo and other factors"""
    
    def __init__(self, team_ratings: TeamRatings):
        self.team_ratings = team_ratings
        self.home_advantage_elo = HOME_ADVANTAGE_ELO
        self.market_shrink_factor = MARKET_SHRINK_FACTOR
    
    def elo_to_win_probability(self, rating_a: float, rating_b: float) -> float:
        """
        Convert Elo rating difference to win probability using logistic formula
        
        Args:
            rating_a: Elo rating of team A
            rating_b: Elo rating of team B
            
        Returns:
            Win probability for team A (0-1)
        """
        return 1.0 / (1.0 + math.pow(10, (rating_b - rating_a) / 400.0))
    
    def predict_match_probabilities(self, home_team: str, away_team: str,
                                   home_form: float = 0.0, away_form: float = 0.0,
                                   home_goal_diff: int = 0, away_goal_diff: int = 0,
                                   market_probabilities: Dict[str, float] = None) -> Dict[str, float]:
        """
        Predict match outcome probabilities
        
        Args:
            home_team: Home team name
            away_team: Away team name
            home_form: Recent form factor for home team (-1 to 1)
            away_form: Recent form factor for away team (-1 to 1)
            home_goal_diff: Goal difference for home team
            away_goal_diff: Goal difference for away team
            market_probabilities: Optional market probabilities for calibration
            
        Returns:
            Dictionary with probabilities for home, draw, away (as percentages)
        """
        # Get base Elo ratings
        home_rating = self.team_ratings.get_rating(home_team)
        away_rating = self.team_ratings.get_rating(away_team)
        
        # Adjust for home advantage (now in Elo points, not factor)
        adjusted_home_rating = home_rating + self.home_advantage_elo
        
        # Adjust for form (each 0.1 form = ~10 Elo points)
        adjusted_home_rating += home_form * 100
        adjusted_away_rating = away_rating + away_form * 100
        
        # Adjust for goal difference (each goal diff = ~5 Elo points, capped at ±5 goals)
        goal_diff_impact = max(-5, min(5, home_goal_diff - away_goal_diff)) * 5
        adjusted_home_rating += goal_diff_impact
        
        # Calculate expected score for home team using proper logistic formula
        home_win_expectation = self.elo_to_win_probability(adjusted_home_rating, adjusted_away_rating)
        
        # Convert to three-way probabilities (home, draw, away)
        # Using a simplified model: stronger expectation = higher win probability
        draw_base = 0.25  # Base draw probability
        
        if home_win_expectation > 0.5:
            # Home favored
            home_prob = 35 + (home_win_expectation - 0.5) * 60  # 35-65%
            draw_prob = draw_base * 100 * (1 - abs(home_win_expectation - 0.5) * 0.5)  # Decreases as favorite gets stronger
            away_prob = 100 - home_prob - draw_prob
        else:
            # Away favored
            away_prob = 35 + (0.5 - home_win_expectation) * 60  # 35-65%
            draw_prob = draw_base * 100 * (1 - abs(home_win_expectation - 0.5) * 0.5)
            home_prob = 100 - away_prob - draw_prob
        
        # Apply calibration caps
        raw_probs = {
            'home': max(MIN_PROBABILITY, min(MAX_PROBABILITY, home_prob)),
            'draw': max(10, min(40, draw_prob)),
            'away': max(MIN_PROBABILITY, min(MAX_PROBABILITY, away_prob))
        }
        
        # Apply market calibration if market probabilities provided
        if market_probabilities and self.market_shrink_factor > 0:
            calibrated_probs = {}
            for outcome in ['home', 'draw', 'away']:
                model_prob = raw_probs[outcome]
                market_prob = market_probabilities.get(outcome, model_prob)
                # Shrink model probability toward market
                calibrated_prob = (1 - self.market_shrink_factor) * model_prob + self.market_shrink_factor * market_prob
                calibrated_probs[outcome] = calibrated_prob
            return calibrated_probs
        
        return raw_probs
