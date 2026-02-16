#!/usr/bin/env python3
"""
Example usage of the soccer betting bot
"""
from soccer_bot.bot import SoccerBettingBot


def example_workflow():
    """Demonstrate a complete betting workflow"""
    
    print("=" * 80)
    print("SOCCER BETTING BOT - EXAMPLE WORKFLOW")
    print("=" * 80)
    
    # Initialize bot with a bankroll
    bot = SoccerBettingBot(bankroll=1000.0)
    
    print("\n1. INITIAL SETUP")
    print("-" * 80)
    print(f"Starting bankroll: ${bot.bankroll}")
    
    # Analyze a match
    print("\n2. ANALYZE MATCH")
    print("-" * 80)
    print("Match: Manchester City vs Liverpool")
    print("Market odds: Home 2.20, Draw 3.40, Away 3.20")
    
    analysis = bot.analyze_match_manual(
        home_team="Manchester City",
        away_team="Liverpool",
        home_odds=2.20,
        draw_odds=3.40,
        away_odds=3.20,
        home_form=0.3,    # Good recent form
        away_form=0.1,    # Slightly positive form
        home_goal_diff=12,
        away_goal_diff=8
    )
    
    print(f"\nTeam Ratings:")
    print(f"  Man City: {analysis['team_ratings']['home']}")
    print(f"  Liverpool: {analysis['team_ratings']['away']}")
    
    print(f"\nModel Probabilities:")
    for outcome, prob in analysis['true_probabilities'].items():
        print(f"  {outcome.capitalize()}: {prob}%")
    
    print(f"\nEdges:")
    for outcome, edge in analysis['edges'].items():
        print(f"  {outcome.capitalize()}: {edge:+.2f}%")
    
    if analysis['recommendation']:
        rec = analysis['recommendation']
        print(f"\n✓ BET RECOMMENDED:")
        print(f"  Type: {rec['bet_type'].upper()}")
        print(f"  Stake: ${rec['stake']}")
        print(f"  Odds: {rec['odds']}")
        print(f"  Edge: {rec['edge']:+.2f}%")
        print(f"  Potential Profit: ${rec['potential_profit']}")
        
        # Place the bet
        print("\n3. PLACE BET")
        print("-" * 80)
        bet_id = bot.place_bet(
            home_team=analysis['home_team'],
            away_team=analysis['away_team'],
            bet_type=rec['bet_type'],
            odds=rec['odds'],
            stake=rec['stake'],
            true_probability=rec['true_probability'],
            market_probability=rec['market_probability'],
            edge=rec['edge'],
            match_date="2026-02-20"
        )
        print(f"Bet placed! ID: {bet_id}")
        print(f"New bankroll: ${bot.bankroll:.2f}")
    else:
        print("\n✗ No bet recommended (insufficient edge)")
    
    # Update ratings after match
    print("\n4. UPDATE RATINGS AFTER MATCH")
    print("-" * 80)
    print("Match result: Manchester City 2-1 Liverpool")
    
    bot.update_ratings_from_result(
        home_team="Manchester City",
        away_team="Liverpool",
        home_score=2,
        away_score=1,
        match_date="2026-02-20"
    )
    
    print(f"Updated ratings:")
    print(f"  Man City: {bot.team_ratings.get_rating('Manchester City'):.0f}")
    print(f"  Liverpool: {bot.team_ratings.get_rating('Liverpool'):.0f}")
    
    # Settle the bet
    if analysis['recommendation'] and analysis['recommendation']['bet_type'] == 'home':
        print("\n5. SETTLE BET")
        print("-" * 80)
        bot.settle_bet(1, 'win')
        print(f"Bet settled as WIN!")
        print(f"Current bankroll: ${bot.bankroll:.2f}")
    
    # Show statistics
    print("\n6. BETTING STATISTICS")
    print("-" * 80)
    stats = bot.get_statistics()
    print(f"Total bets: {stats['total_bets']}")
    print(f"Win rate: {stats['win_rate']:.1f}%")
    print(f"Total P/L: ${stats['total_profit_loss']:.2f}")
    print(f"ROI: {stats['roi']:.2f}%")
    print(f"Current bankroll: ${stats['current_bankroll']:.2f}")
    
    print("\n" + "=" * 80)
    print("EXAMPLE COMPLETE")
    print("=" * 80)


def multiple_matches_example():
    """Example with multiple matches"""
    
    print("\n" + "=" * 80)
    print("MULTIPLE MATCHES EXAMPLE")
    print("=" * 80)
    
    bot = SoccerBettingBot(bankroll=1000.0)
    
    matches = [
        {
            'home': 'Barcelona', 'away': 'Real Madrid',
            'home_odds': 2.30, 'draw_odds': 3.20, 'away_odds': 3.10,
            'home_form': 0.4, 'away_form': 0.2
        },
        {
            'home': 'Bayern Munich', 'away': 'Dortmund',
            'home_odds': 1.80, 'draw_odds': 3.60, 'away_odds': 4.50,
            'home_form': 0.5, 'away_form': -0.1
        },
        {
            'home': 'PSG', 'away': 'Lyon',
            'home_odds': 1.65, 'draw_odds': 3.80, 'away_odds': 5.50,
            'home_form': 0.3, 'away_form': -0.3
        }
    ]
    
    recommendations = []
    
    for i, match in enumerate(matches, 1):
        print(f"\nMatch {i}: {match['home']} vs {match['away']}")
        print("-" * 80)
        
        analysis = bot.analyze_match_manual(
            home_team=match['home'],
            away_team=match['away'],
            home_odds=match['home_odds'],
            draw_odds=match['draw_odds'],
            away_odds=match['away_odds'],
            home_form=match['home_form'],
            away_form=match['away_form']
        )
        
        if analysis['recommendation']:
            rec = analysis['recommendation']
            print(f"✓ BET: {rec['bet_type'].upper()} @ {rec['odds']} - Stake: ${rec['stake']:.2f} (Edge: {rec['edge']:+.2f}%)")
            recommendations.append((analysis, rec))
        else:
            max_edge = max(analysis['edges'].values())
            print(f"✗ NO BET (Max edge: {max_edge:+.2f}%)")
    
    print(f"\n{'=' * 80}")
    print(f"SUMMARY: {len(recommendations)} recommended bets out of {len(matches)} matches")
    print(f"Total recommended stake: ${sum(rec['stake'] for _, rec in recommendations):.2f}")
    print(f"{'=' * 80}")


if __name__ == '__main__':
    example_workflow()
    print("\n" * 2)
    multiple_matches_example()
