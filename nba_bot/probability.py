"""
NBA probability calculation utilities.

NBA markets are 2-way (home/away) — no draw.
Supports both American moneyline odds and decimal odds as inputs.
"""
from typing import Dict


def moneyline_to_implied_prob(ml: float) -> float:
    """
    Convert American moneyline odds to implied probability (%).

    Args:
        ml: American moneyline (e.g. -150, +130)

    Returns:
        Implied probability as a percentage (0-100)
    """
    if ml == 0:
        return 0.0
    if ml > 0:
        return (100.0 / (ml + 100.0)) * 100.0
    else:
        abs_ml = abs(ml)
        return (abs_ml / (abs_ml + 100.0)) * 100.0


def decimal_to_implied_prob(odds: float) -> float:
    """
    Convert decimal odds to implied probability (%).

    Args:
        odds: Decimal odds (e.g. 1.67)

    Returns:
        Implied probability as a percentage (0-100)
    """
    if odds <= 1.0:
        return 0.0
    return (1.0 / odds) * 100.0


def remove_vig_two_way(home_prob: float, away_prob: float) -> Dict[str, float]:
    """
    Remove bookmaker's vig from a 2-way market.

    Args:
        home_prob: Home implied probability (%)
        away_prob: Away implied probability (%)

    Returns:
        Dictionary with fair home/away probabilities (sum to 100%)
    """
    total = home_prob + away_prob
    if total <= 0:
        return {'home': 50.0, 'away': 50.0}
    return {
        'home': (home_prob / total) * 100.0,
        'away': (away_prob / total) * 100.0,
    }


def implied_prob_to_decimal(probability: float) -> float:
    """
    Convert probability (%) to decimal odds.

    Args:
        probability: Probability as percentage (0-100)

    Returns:
        Decimal odds
    """
    if probability <= 0.0 or probability >= 100.0:
        return 0.0
    return 100.0 / probability


def implied_prob_to_moneyline(probability: float) -> float:
    """
    Convert probability (%) to American moneyline odds.

    Args:
        probability: Probability as percentage (0-100)

    Returns:
        American moneyline odds (negative = favourite)
    """
    if probability <= 0.0 or probability >= 100.0:
        return 0.0
    p = probability / 100.0
    if p >= 0.5:
        return -(p / (1.0 - p)) * 100.0
    else:
        return ((1.0 - p) / p) * 100.0
