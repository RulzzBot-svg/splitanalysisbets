"""
Team rating and prediction model using Elo ratings
"""
import math
from typing import Dict, Tuple
from soccer_bot.config import HOME_ADVANTAGE, ELO_K_FACTOR, INITIAL_ELO


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
        self.home_advantage = HOME_ADVANTAGE
    
    def predict_match_probabilities(self, home_team: str, away_team: str,
                                   home_form: float = 0.0, away_form: float = 0.0,
                                   home_goal_diff: int = 0, away_goal_diff: int = 0) -> Dict[str, float]:
        """
        Predict match outcome probabilities
        
        Args:
            home_team: Home team name
            away_team: Away team name
            home_form: Recent form factor for home team (-1 to 1)
            away_form: Recent form factor for away team (-1 to 1)
            home_goal_diff: Goal difference for home team
            away_goal_diff: Goal difference for away team
            
        Returns:
            Dictionary with probabilities for home, draw, away (as percentages)
        """
        # Get base Elo ratings
        home_rating = self.team_ratings.get_rating(home_team)
        away_rating = self.team_ratings.get_rating(away_team)
        
        # Adjust for home advantage
        adjusted_home_rating = home_rating + (self.home_advantage * 400)
        
        # Adjust for form (each 0.1 form = ~10 Elo points)
        adjusted_home_rating += home_form * 100
        adjusted_away_rating = away_rating + away_form * 100
        
        # Adjust for goal difference (each goal diff = ~5 Elo points, capped at ±5 goals)
        goal_diff_impact = max(-5, min(5, home_goal_diff - away_goal_diff)) * 5
        adjusted_home_rating += goal_diff_impact
        
        # Calculate expected score for home team
        home_win_expectation = self.team_ratings.expected_score(adjusted_home_rating, adjusted_away_rating)
        
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
        
        return {
            'home': max(5, min(85, home_prob)),  # Cap between 5-85%
            'draw': max(10, min(40, draw_prob)),  # Cap between 10-40%
            'away': max(5, min(85, away_prob))    # Cap between 5-85%
        }
