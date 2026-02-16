"""
Probability calculation utilities
"""
from typing import Dict


def odds_to_implied_probability(odds: float) -> float:
    """
    Convert decimal odds to implied probability
    
    Args:
        odds: Decimal odds (e.g., 2.50)
        
    Returns:
        Implied probability as percentage (0-100)
    """
    if odds <= 1.0:
        return 0.0
    return (1.0 / odds) * 100.0


def implied_probability_to_odds(probability: float) -> float:
    """
    Convert probability to decimal odds
    
    Args:
        probability: Probability as percentage (0-100)
        
    Returns:
        Decimal odds
    """
    if probability <= 0.0 or probability >= 100.0:
        return 0.0
    return 100.0 / probability


def normalize_probabilities(home_prob: float, draw_prob: float, away_prob: float) -> Dict[str, float]:
    """
    Normalize probabilities to sum to 100%
    
    Args:
        home_prob: Home win probability
        draw_prob: Draw probability
        away_prob: Away win probability
        
    Returns:
        Dictionary with normalized probabilities
    """
    total = home_prob + draw_prob + away_prob
    
    if total == 0:
        return {'home': 33.33, 'draw': 33.33, 'away': 33.33}
    
    return {
        'home': (home_prob / total) * 100.0,
        'draw': (draw_prob / total) * 100.0,
        'away': (away_prob / total) * 100.0
    }


def remove_bookmaker_margin(home_prob: float, draw_prob: float, away_prob: float) -> Dict[str, float]:
    """
    Remove bookmaker's margin from implied probabilities
    
    Args:
        home_prob: Home win implied probability (%)
        draw_prob: Draw implied probability (%)
        away_prob: Away win implied probability (%)
        
    Returns:
        Dictionary with fair probabilities (bookmaker margin removed)
    """
    total = home_prob + draw_prob + away_prob
    
    # If total is close to 100%, no margin to remove
    if total <= 100.0:
        return {'home': home_prob, 'draw': draw_prob, 'away': away_prob}
    
    # Normalize to remove the overround
    return {
        'home': (home_prob / total) * 100.0,
        'draw': (draw_prob / total) * 100.0,
        'away': (away_prob / total) * 100.0
    }
