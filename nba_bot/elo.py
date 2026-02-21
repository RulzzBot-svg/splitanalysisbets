"""
Standard Elo rating helpers for NBA game outcomes.

Formulas:
    E_h = 1 / (1 + 10^(-(R_h + H - R_a) / 400))
    R_h' = R_h + K * (S_h - E_h)
    R_a' = R_a + K * ((1 - S_h) - (1 - E_h))

Default constants:
    K = 20  (simple, stable)
    H = 50  (home-court advantage in Elo points)
"""


def expected_score(r_home: float, r_away: float, home_adv: float = 50.0) -> float:
    """
    Return the expected win probability for the home team.

    Args:
        r_home: Current Elo rating of the home team.
        r_away: Current Elo rating of the away team.
        home_adv: Home-court advantage expressed in Elo points (default 50).

    Returns:
        Float in (0, 1) — probability that the home team wins.
    """
    return 1.0 / (1.0 + 10.0 ** (-((r_home + home_adv - r_away) / 400.0)))


def update_elo(
    r_home: float,
    r_away: float,
    home_won: bool,
    k: float = 20.0,
    home_adv: float = 50.0,
):
    """
    Apply a single Elo update after an NBA game.

    Args:
        r_home: Pre-game Elo of the home team.
        r_away: Pre-game Elo of the away team.
        home_won: True if the home team won.
        k: K-factor (controls how fast ratings change, default 20).
        home_adv: Home-court advantage in Elo points (default 50).

    Returns:
        (new_r_home, new_r_away) — updated Elo ratings.
    """
    e_home = expected_score(r_home, r_away, home_adv=home_adv)
    s_home = 1.0 if home_won else 0.0
    r_home_new = r_home + k * (s_home - e_home)
    r_away_new = r_away + k * ((1.0 - s_home) - (1.0 - e_home))
    return r_home_new, r_away_new
