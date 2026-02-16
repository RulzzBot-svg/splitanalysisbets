"""
Kelly criterion betting strategy
"""
from typing import Optional


def kelly_criterion(probability: float, odds: float, fraction: float = 0.5) -> float:
    """
    Calculate bet size using Kelly criterion
    
    Args:
        probability: True win probability (0-1)
        odds: Decimal odds offered
        fraction: Fraction of Kelly to use (0.5 = Half Kelly)
        
    Returns:
        Fraction of bankroll to bet (0-1)
    """
    if probability <= 0 or probability >= 1 or odds <= 1:
        return 0.0
    
    # Kelly formula: f = (bp - q) / b
    # where b = odds - 1, p = probability, q = 1 - probability
    b = odds - 1
    q = 1 - probability
    
    kelly_fraction = (b * probability - q) / b
    
    # Apply fractional Kelly (e.g., Half Kelly)
    kelly_fraction *= fraction
    
    # Don't bet if Kelly is negative or zero
    if kelly_fraction <= 0:
        return 0.0
    
    # Cap at reasonable maximum (25% of bankroll even with Half Kelly)
    return min(kelly_fraction, 0.25)


def calculate_bet_size(bankroll: float, probability: float, odds: float,
                      fraction: float = 0.5) -> float:
    """
    Calculate actual bet amount using Half Kelly
    
    Args:
        bankroll: Total bankroll
        probability: True win probability (0-1)
        odds: Decimal odds offered
        fraction: Fraction of Kelly to use (default 0.5 for Half Kelly)
        
    Returns:
        Bet amount in currency
    """
    kelly_frac = kelly_criterion(probability, odds, fraction)
    return bankroll * kelly_frac


def calculate_edge(true_probability: float, market_probability: float) -> float:
    """
    Calculate betting edge
    
    Args:
        true_probability: Estimated true probability (%)
        market_probability: Market implied probability (%)
        
    Returns:
        Edge as percentage points
    """
    return true_probability - market_probability


def should_bet(edge: float, threshold: float = 2.5) -> bool:
    """
    Determine if bet should be placed based on edge threshold
    
    Args:
        edge: Calculated edge (%)
        threshold: Minimum edge required (%)
        
    Returns:
        True if bet should be placed
    """
    return edge >= threshold
