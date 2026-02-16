#!/usr/bin/env python3
"""
Simple tests for the soccer betting bot
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from soccer_bot.probability import odds_to_implied_probability, remove_bookmaker_margin
from soccer_bot.betting import calculate_edge, should_bet, kelly_criterion
from soccer_bot.model import TeamRatings, PredictionModel


def test_probability_conversion():
    """Test odds to probability conversion"""
    print("Testing probability conversion...")
    
    # Test decimal odds conversion
    assert abs(odds_to_implied_probability(2.0) - 50.0) < 0.01
    assert abs(odds_to_implied_probability(4.0) - 25.0) < 0.01
    assert abs(odds_to_implied_probability(1.5) - 66.67) < 0.01
    
    print("✓ Probability conversion works")


def test_bookmaker_margin():
    """Test bookmaker margin removal"""
    print("Testing bookmaker margin removal...")
    
    # Odds: Home 2.0, Draw 3.0, Away 4.0
    home_prob = odds_to_implied_probability(2.0)  # 50%
    draw_prob = odds_to_implied_probability(3.0)  # 33.33%
    away_prob = odds_to_implied_probability(4.0)  # 25%
    # Total = 108.33% (8.33% overround/margin)
    
    fair_probs = remove_bookmaker_margin(home_prob, draw_prob, away_prob)
    
    # After removing margin, should sum to 100%
    total = fair_probs['home'] + fair_probs['draw'] + fair_probs['away']
    assert abs(total - 100.0) < 0.01
    
    print("✓ Bookmaker margin removal works")


def test_edge_calculation():
    """Test edge calculation"""
    print("Testing edge calculation...")
    
    edge = calculate_edge(55.0, 50.0)
    assert edge == 5.0
    
    edge = calculate_edge(45.0, 50.0)
    assert edge == -5.0
    
    print("✓ Edge calculation works")


def test_bet_threshold():
    """Test betting threshold"""
    print("Testing bet threshold...")
    
    assert should_bet(3.0, 2.5) == True
    assert should_bet(2.0, 2.5) == False
    assert should_bet(2.5, 2.5) == True
    
    print("✓ Bet threshold works")


def test_kelly_criterion():
    """Test Kelly criterion calculation"""
    print("Testing Kelly criterion...")
    
    # Example: 60% win probability, odds of 2.0
    # Kelly = (2.0 * 0.6 - 1) / (2.0 - 1) = 0.2 / 1.0 = 0.2 (20%)
    # Half-Kelly = 0.1 (10%)
    kelly_frac = kelly_criterion(0.6, 2.0, fraction=0.5)
    assert abs(kelly_frac - 0.1) < 0.01
    
    # No edge case: 50% probability, odds 2.0
    # Kelly = (2.0 * 0.5 - 1) / (2.0 - 1) = 0 / 1.0 = 0
    kelly_frac = kelly_criterion(0.5, 2.0, fraction=0.5)
    assert kelly_frac == 0.0
    
    print("✓ Kelly criterion works")


def test_elo_ratings():
    """Test Elo rating system"""
    print("Testing Elo ratings...")
    
    ratings = TeamRatings()
    
    # Initial ratings
    assert ratings.get_rating("Team A") == 1500
    assert ratings.get_rating("Team B") == 1500
    
    # Simulate Team A beating Team B
    ratings.update_ratings_after_match("Team A", "Team B", 2, 0)
    
    # Team A should have higher rating now
    assert ratings.get_rating("Team A") > 1500
    assert ratings.get_rating("Team B") < 1500
    
    # Ratings should be symmetric
    rating_diff = ratings.get_rating("Team A") - ratings.get_rating("Team B")
    assert rating_diff > 0
    
    print("✓ Elo ratings work")


def test_prediction_model():
    """Test prediction model"""
    print("Testing prediction model...")
    
    ratings = TeamRatings()
    model = PredictionModel(ratings)
    
    # Predict match with equal teams
    probs = model.predict_match_probabilities("Team A", "Team B")
    
    # Check that probabilities are valid
    assert 0 < probs['home'] < 100
    assert 0 < probs['draw'] < 100
    assert 0 < probs['away'] < 100
    
    # Home advantage should make home more likely than away (equal teams)
    assert probs['home'] > probs['away']
    
    print("✓ Prediction model works")


def test_full_workflow():
    """Test a complete betting workflow"""
    print("Testing full workflow...")
    
    from soccer_bot.bot import SoccerBettingBot
    
    # Create bot
    bot = SoccerBettingBot(bankroll=1000.0)
    
    # Analyze a match
    analysis = bot.analyze_match_manual(
        home_team="Team X",
        away_team="Team Y",
        home_odds=2.0,
        draw_odds=3.0,
        away_odds=4.0
    )
    
    # Check analysis structure
    assert 'home_team' in analysis
    assert 'away_team' in analysis
    assert 'market_probabilities' in analysis
    assert 'true_probabilities' in analysis
    assert 'edges' in analysis
    assert 'recommendation' in analysis
    
    # If there's a recommendation, place a bet
    if analysis['recommendation']:
        rec = analysis['recommendation']
        bet_id = bot.place_bet(
            home_team=analysis['home_team'],
            away_team=analysis['away_team'],
            bet_type=rec['bet_type'],
            odds=rec['odds'],
            stake=rec['stake'],
            true_probability=rec['true_probability'],
            market_probability=rec['market_probability'],
            edge=rec['edge']
        )
        
        assert bet_id > 0
        
        # Settle the bet
        bot.settle_bet(bet_id, 'win')
        
        # Check statistics
        stats = bot.get_statistics()
        assert stats['total_bets'] > 0
    
    print("✓ Full workflow works")


def run_all_tests():
    """Run all tests"""
    print("=" * 80)
    print("RUNNING TESTS")
    print("=" * 80)
    print()
    
    tests = [
        test_probability_conversion,
        test_bookmaker_margin,
        test_edge_calculation,
        test_bet_threshold,
        test_kelly_criterion,
        test_elo_ratings,
        test_prediction_model,
        test_full_workflow
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
