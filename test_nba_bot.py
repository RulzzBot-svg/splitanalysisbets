#!/usr/bin/env python3
"""
Tests for the NBA betting bot.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nba_bot.probability import (
    moneyline_to_implied_prob,
    decimal_to_implied_prob,
    remove_vig_two_way,
    implied_prob_to_moneyline,
)
from nba_bot.betting import calculate_edge, should_bet, kelly_criterion
from nba_bot.model import NBATeamRatings, NBAModel


# ---------------------------------------------------------------------------
# Probability tests
# ---------------------------------------------------------------------------

def test_moneyline_to_implied_prob():
    """Moneyline → implied probability conversion."""
    print("Testing moneyline → implied probability...")

    # Favourite: -150  → 150/250 = 60%
    assert abs(moneyline_to_implied_prob(-150) - 60.0) < 0.01

    # Underdog: +130  → 100/230 ≈ 43.48%
    assert abs(moneyline_to_implied_prob(130) - 43.478) < 0.01

    # Even money: +100 = -100  → 50%
    assert abs(moneyline_to_implied_prob(100) - 50.0) < 0.01
    assert abs(moneyline_to_implied_prob(-100) - 50.0) < 0.01

    print("✓ Moneyline → implied probability works")


def test_decimal_to_implied_prob():
    """Decimal odds → implied probability conversion."""
    print("Testing decimal → implied probability...")

    assert abs(decimal_to_implied_prob(2.0) - 50.0) < 0.01
    assert abs(decimal_to_implied_prob(4.0) - 25.0) < 0.01
    assert abs(decimal_to_implied_prob(1.5) - 66.67) < 0.01

    print("✓ Decimal → implied probability works")


def test_remove_vig_two_way():
    """Vig removal sums to 100%."""
    print("Testing 2-way vig removal...")

    # Typical market: home -150, away +130 → 60% + 43.48% = 103.48% total
    home_imp = moneyline_to_implied_prob(-150)  # 60.0
    away_imp = moneyline_to_implied_prob(130)   # ≈43.48
    fair = remove_vig_two_way(home_imp, away_imp)

    assert abs(fair['home'] + fair['away'] - 100.0) < 0.01
    assert fair['home'] > fair['away']  # home is the favourite

    print("✓ 2-way vig removal works")


# ---------------------------------------------------------------------------
# Betting strategy tests
# ---------------------------------------------------------------------------

def test_edge_calculation():
    """Edge = true_prob - market_prob."""
    print("Testing edge calculation...")

    assert calculate_edge(55.0, 50.0) == 5.0
    assert calculate_edge(45.0, 50.0) == -5.0

    print("✓ Edge calculation works")


def test_should_bet():
    """Threshold filter."""
    print("Testing should_bet threshold...")

    assert should_bet(2.0, 1.0) is True
    assert should_bet(0.5, 1.0) is False
    assert should_bet(1.0, 1.0) is True

    print("✓ should_bet threshold works")


def test_kelly_criterion():
    """Kelly criterion sanity checks."""
    print("Testing Kelly criterion...")

    # 60% probability, 2.0 decimal odds, half-Kelly
    # Kelly = (1*0.6 - 0.4)/1 = 0.2; half = 0.1; capped at 5%
    k = kelly_criterion(0.6, 2.0, fraction=0.5)
    assert k == 0.05  # capped at 5%

    # No edge: 50% probability at 2.0 odds → 0
    k = kelly_criterion(0.5, 2.0, fraction=0.5)
    assert k == 0.0

    print("✓ Kelly criterion works")


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

def test_elo_ratings():
    """Elo ratings update correctly after a game."""
    print("Testing NBA Elo ratings...")

    ratings = NBATeamRatings()

    # Both teams start at 1500
    assert ratings.get_rating("Team A") == 1500
    assert ratings.get_rating("Team B") == 1500

    # Team A wins at home
    ratings.update_ratings_after_game("Team A", "Team B", home_won=True)

    assert ratings.get_rating("Team A") > 1500
    assert ratings.get_rating("Team B") < 1500

    print("✓ NBA Elo ratings work")


def test_prediction_model_two_way():
    """Model returns only home/away probabilities (no draw)."""
    print("Testing NBA 2-way prediction model...")

    ratings = NBATeamRatings()
    model = NBAModel(ratings)

    probs = model.predict_win_prob("Team A", "Team B")

    assert 'home' in probs
    assert 'away' in probs
    assert 'draw' not in probs
    assert abs(probs['home'] + probs['away'] - 100.0) < 0.01
    assert 0 < probs['home'] < 100
    assert 0 < probs['away'] < 100

    # Home court advantage → home team more likely to win with equal Elo
    assert probs['home'] > probs['away']

    print("✓ NBA 2-way prediction model works")


def test_prediction_model_adjustments():
    """Back-to-back and star-out flags reduce the affected team's probability."""
    print("Testing NBA model adjustments...")

    ratings = NBATeamRatings()
    model = NBAModel(ratings)

    base = model.predict_win_prob("Team A", "Team B")

    # Home team on B2B → home probability decreases
    b2b = model.predict_win_prob("Team A", "Team B", home_b2b=True)
    assert b2b['home'] < base['home']

    # Away star out → away probability decreases (home probability increases)
    star = model.predict_win_prob("Team A", "Team B", away_star_out=True)
    assert star['home'] > base['home']

    # Rest differential: home has more rest → home probability increases
    rest = model.predict_win_prob("Team A", "Team B", rest_diff=2)
    assert rest['home'] > base['home']

    print("✓ NBA model adjustments work")


# ---------------------------------------------------------------------------
# Full workflow test
# ---------------------------------------------------------------------------

def test_full_workflow():
    """End-to-end workflow: analyse → place bet → settle → stats."""
    print("Testing full NBA workflow...")

    import tempfile
    import os
    from nba_bot.bot import NBABettingBot

    fd, tmp_db = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    try:
        bot = NBABettingBot(bankroll=1000.0, db_path=tmp_db)
    except Exception:
        bot = NBABettingBot(bankroll=1000.0)

    # Analyse a game (home team is a strong favourite)
    bot.team_ratings.update_rating("Lakers", 1650)
    bot.team_ratings.update_rating("Pistons", 1350)

    analysis = bot.analyze_game(
        home_team="Lakers",
        away_team="Pistons",
        home_ml=-200,
        away_ml=170,
    )

    assert 'home_team' in analysis
    assert 'away_team' in analysis
    assert 'market_probabilities' in analysis
    assert 'true_probabilities' in analysis
    assert 'edges' in analysis
    assert 'recommendation' in analysis
    assert 'draw' not in analysis['market_probabilities']
    assert 'draw' not in analysis['true_probabilities']

    # Lakers should be recommended (high model probability)
    assert analysis['recommendation'] is not None
    assert analysis['recommendation']['bet_type'] == 'home'

    rec = analysis['recommendation']
    bet_id = bot.place_bet(
        home_team=analysis['home_team'],
        away_team=analysis['away_team'],
        bet_type=rec['bet_type'],
        odds=rec['odds'],
        stake=rec['stake'],
        true_probability=rec['true_probability'],
        market_probability=rec['market_probability'],
        edge=rec['edge'],
    )

    assert bet_id > 0
    assert bot.bankroll < 1000.0  # stake deducted

    bot.settle_bet(bet_id, 'win')

    stats = bot.get_statistics()
    assert stats['total_bets'] == 1
    assert stats['wins'] == 1

    # Cleanup temp db
    try:
        os.remove(tmp_db)
    except Exception:
        pass

    print("✓ Full NBA workflow works")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all_tests():
    """Run all NBA bot tests."""
    print("=" * 80)
    print("RUNNING NBA BOT TESTS")
    print("=" * 80)
    print()

    tests = [
        test_moneyline_to_implied_prob,
        test_decimal_to_implied_prob,
        test_remove_vig_two_way,
        test_edge_calculation,
        test_should_bet,
        test_kelly_criterion,
        test_elo_ratings,
        test_prediction_model_two_way,
        test_prediction_model_adjustments,
        test_full_workflow,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1

    print()
    print("=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)

    if failed > 0:
        sys.exit(1)


if __name__ == '__main__':
    run_all_tests()
