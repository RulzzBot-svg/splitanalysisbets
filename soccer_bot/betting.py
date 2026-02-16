"""
Kelly criterion betting strategy
"""
from typing import Optional
from soccer_bot.config import KELLY_FRACTION, MAX_STAKE_PERCENT, FLAT_STAKE_PERCENT, USE_FLAT_STAKING


def kelly_criterion(probability: float, odds: float, fraction: float = None) -> float:
    """
    Calculate bet size using Kelly criterion
    
    Args:
        probability: True win probability (0-1)
        odds: Decimal odds offered
        fraction: Fraction of Kelly to use (defaults to config KELLY_FRACTION, e.g., 0.25 = Quarter Kelly)
        
    Returns:
        Fraction of bankroll to bet (0-1)
    """
    if fraction is None:
        fraction = KELLY_FRACTION
        
    if probability <= 0 or probability >= 1 or odds <= 1:
        return 0.0
    
    # Kelly formula: f = (bp - q) / b
    # where b = odds - 1, p = probability, q = 1 - probability
    b = odds - 1
    q = 1 - probability
    
    kelly_fraction = (b * probability - q) / b
    
    # Apply fractional Kelly (e.g., Quarter Kelly for more conservative)
    kelly_fraction *= fraction
    
    # Don't bet if Kelly is negative or zero
    if kelly_fraction <= 0:
        return 0.0
    
    # Cap at maximum stake percentage
    max_stake_frac = MAX_STAKE_PERCENT / 100.0
    return min(kelly_fraction, max_stake_frac)


def calculate_bet_size(bankroll: float, probability: float, odds: float,
                      fraction: float = None, use_flat: bool = None) -> float:
    """
    Calculate actual bet amount using Kelly or flat staking
    
    Args:
        bankroll: Total bankroll
        probability: True win probability (0-1)
        odds: Decimal odds offered
        fraction: Fraction of Kelly to use (default uses config KELLY_FRACTION)
        use_flat: Use flat staking instead of Kelly (default uses config USE_FLAT_STAKING)
        
    Returns:
        Bet amount in currency
    """
    if use_flat is None:
        use_flat = USE_FLAT_STAKING
    
    if use_flat:
        # Flat staking: fixed percentage of bankroll
        return bankroll * (FLAT_STAKE_PERCENT / 100.0)
    else:
        # Kelly criterion staking
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
