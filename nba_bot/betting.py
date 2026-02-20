"""
Betting strategy utilities for NBA bot (Kelly criterion + flat staking).
"""
from nba_bot.config import KELLY_FRACTION, MAX_STAKE_PERCENT, FLAT_STAKE_PERCENT, USE_FLAT_STAKING


def kelly_criterion(probability: float, odds: float, fraction: float = None) -> float:
    """
    Calculate bet size fraction using Kelly criterion.

    Args:
        probability: True win probability (0-1)
        odds: Decimal odds offered
        fraction: Fraction of Kelly to use (defaults to config KELLY_FRACTION)

    Returns:
        Fraction of bankroll to bet (0-1)
    """
    if fraction is None:
        fraction = KELLY_FRACTION

    if probability <= 0 or probability >= 1 or odds <= 1:
        return 0.0

    b = odds - 1.0
    q = 1.0 - probability
    kelly_frac = (b * probability - q) / b

    kelly_frac *= fraction

    if kelly_frac <= 0:
        return 0.0

    return min(kelly_frac, MAX_STAKE_PERCENT / 100.0)


def calculate_bet_size(bankroll: float, probability: float, odds: float,
                       fraction: float = None, use_flat: bool = None) -> float:
    """
    Calculate actual bet amount using Kelly or flat staking.

    Args:
        bankroll: Total bankroll
        probability: True win probability (0-1)
        odds: Decimal odds offered
        fraction: Fraction of Kelly to use
        use_flat: Use flat staking instead of Kelly

    Returns:
        Bet amount in currency
    """
    if use_flat is None:
        use_flat = USE_FLAT_STAKING

    if use_flat:
        return bankroll * (FLAT_STAKE_PERCENT / 100.0)
    else:
        kelly_frac = kelly_criterion(probability, odds, fraction)
        return bankroll * kelly_frac


def calculate_edge(true_probability: float, market_probability: float) -> float:
    """
    Calculate betting edge (true_prob - market_prob) in percentage points.
    """
    return true_probability - market_probability


def should_bet(edge: float, threshold: float = 1.0) -> bool:
    """
    Determine if bet should be placed based on edge threshold.

    Args:
        edge: Calculated edge (%)
        threshold: Minimum edge required (%)

    Returns:
        True if bet should be placed
    """
    return edge >= threshold
