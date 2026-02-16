#!/usr/bin/env python3
"""
Command-line interface for soccer betting bot
"""
import argparse
import sys
from soccer_bot.bot import SoccerBettingBot
from soccer_bot.config import BANKROLL, EDGE_THRESHOLD


def print_analysis(analysis):
    """Print match analysis in a readable format"""
    print(f"\n{'=' * 70}")
    print(f"MATCH ANALYSIS: {analysis['home_team']} vs {analysis['away_team']}")
    print(f"{'=' * 70}")
    
    print("\nTeam Elo Ratings:")
    print(f"  {analysis['home_team']}: {analysis['team_ratings']['home']}")
    print(f"  {analysis['away_team']}: {analysis['team_ratings']['away']}")
    
    print("\nMarket Probabilities (implied from odds):")
    print(f"  Home: {analysis['market_probabilities']['home']}%")
    print(f"  Draw: {analysis['market_probabilities']['draw']}%")
    print(f"  Away: {analysis['market_probabilities']['away']}%")
    
    print("\nModel (True) Probabilities:")
    print(f"  Home: {analysis['true_probabilities']['home']}%")
    print(f"  Draw: {analysis['true_probabilities']['draw']}%")
    print(f"  Away: {analysis['true_probabilities']['away']}%")
    
    print("\nEdges (True - Market):")
    print(f"  Home: {analysis['edges']['home']:+.2f}%")
    print(f"  Draw: {analysis['edges']['draw']:+.2f}%")
    print(f"  Away: {analysis['edges']['away']:+.2f}%")
    
    if analysis['recommendation']:
        rec = analysis['recommendation']
        print(f"\n{'*' * 70}")
        print("BETTING RECOMMENDATION:")
        print(f"{'*' * 70}")
        print(f"  Bet Type: {rec['bet_type'].upper()}")
        print(f"  Odds: {rec['odds']}")
        print(f"  Recommended Stake: ${rec['stake']:.2f}")
        print(f"  Edge: {rec['edge']:+.2f}%")
        print(f"  True Probability: {rec['true_probability']:.2f}%")
        print(f"  Market Probability: {rec['market_probability']:.2f}%")
        print(f"  Potential Return: ${rec['potential_return']:.2f}")
        print(f"  Potential Profit: ${rec['potential_profit']:.2f}")
        print(f"{'*' * 70}")
    else:
        print(f"\nNo bet recommended (edge below {EDGE_THRESHOLD}% threshold)")
    
    print()


def analyze_command(args):
    """Handle analyze command"""
    bot = SoccerBettingBot(bankroll=args.bankroll)
    
    analysis = bot.analyze_match_manual(
        home_team=args.home_team,
        away_team=args.away_team,
        home_odds=args.home_odds,
        draw_odds=args.draw_odds,
        away_odds=args.away_odds,
        home_form=args.home_form,
        away_form=args.away_form,
        home_goal_diff=args.home_gd,
        away_goal_diff=args.away_gd
    )
    
    print_analysis(analysis)
    
    # Ask if user wants to place the bet
    if analysis['recommendation'] and args.interactive:
        response = input("\nPlace this bet? (yes/no): ").strip().lower()
        if response in ['yes', 'y']:
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
            print(f"\n✓ Bet placed! Bet ID: {bet_id}")
            print(f"  New bankroll: ${bot.bankroll:.2f}")


def bet_command(args):
    """Handle bet command"""
    bot = SoccerBettingBot(bankroll=args.bankroll)
    
    bet_id = bot.place_bet(
        home_team=args.home_team,
        away_team=args.away_team,
        bet_type=args.bet_type,
        odds=args.odds,
        stake=args.stake,
        true_probability=args.true_prob,
        market_probability=args.market_prob,
        edge=args.true_prob - args.market_prob,
        match_date=args.match_date
    )
    
    print(f"✓ Bet placed! Bet ID: {bet_id}")
    print(f"  New bankroll: ${bot.bankroll:.2f}")


def settle_command(args):
    """Handle settle command"""
    bot = SoccerBettingBot()
    
    bot.settle_bet(args.bet_id, args.result)
    print(f"✓ Bet {args.bet_id} settled as {args.result}")
    print(f"  Current bankroll: ${bot.bankroll:.2f}")


def update_ratings_command(args):
    """Handle update-ratings command"""
    bot = SoccerBettingBot()
    
    bot.update_ratings_from_result(
        home_team=args.home_team,
        away_team=args.away_team,
        home_score=args.home_score,
        away_score=args.away_score,
        match_date=args.match_date
    )
    
    print(f"✓ Ratings updated for {args.home_team} vs {args.away_team}")
    print(f"  {args.home_team}: {bot.team_ratings.get_rating(args.home_team):.0f}")
    print(f"  {args.away_team}: {bot.team_ratings.get_rating(args.away_team):.0f}")


def stats_command(args):
    """Handle stats command"""
    bot = SoccerBettingBot()
    
    stats = bot.get_statistics()
    
    print(f"\n{'=' * 70}")
    print("BETTING STATISTICS")
    print(f"{'=' * 70}")
    print(f"Current Bankroll: ${stats['current_bankroll']:.2f}")
    print(f"\nTotal Bets: {stats['total_bets']}")
    print(f"  Settled: {stats['settled_bets']}")
    print(f"  Pending: {stats['pending_bets']}")
    print(f"\nResults:")
    print(f"  Wins: {stats['wins']}")
    print(f"  Losses: {stats['losses']}")
    print(f"  Win Rate: {stats['win_rate']:.1f}%")
    print(f"\nFinancials:")
    print(f"  Total Staked: ${stats['total_staked']:.2f}")
    print(f"  Total P/L: ${stats['total_profit_loss']:.2f}")
    print(f"  ROI: {stats['roi']:.2f}%")
    print()


def list_bets_command(args):
    """Handle list-bets command"""
    bot = SoccerBettingBot()
    
    if args.pending:
        bets = bot.get_pending_bets()
        print(f"\n{'=' * 70}")
        print(f"PENDING BETS ({len(bets)})")
        print(f"{'=' * 70}")
    else:
        bets = bot.get_all_bets()
        print(f"\n{'=' * 70}")
        print(f"ALL BETS ({len(bets)})")
        print(f"{'=' * 70}")
    
    if not bets:
        print("No bets found.")
        return
    
    for bet in bets:
        print(f"\nBet ID: {bet['id']}")
        print(f"  Match: {bet['home_team']} vs {bet['away_team']}")
        print(f"  Type: {bet['bet_type']}")
        print(f"  Odds: {bet['odds']}")
        print(f"  Stake: ${bet['stake']:.2f}")
        print(f"  Edge: {bet['edge']:+.2f}%")
        if bet['result']:
            print(f"  Result: {bet['result']}")
            print(f"  P/L: ${bet['profit_loss']:+.2f}")
    print()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Soccer Betting Decision Bot',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a match')
    analyze_parser.add_argument('home_team', help='Home team name')
    analyze_parser.add_argument('away_team', help='Away team name')
    analyze_parser.add_argument('home_odds', type=float, help='Home win odds (decimal)')
    analyze_parser.add_argument('draw_odds', type=float, help='Draw odds (decimal)')
    analyze_parser.add_argument('away_odds', type=float, help='Away win odds (decimal)')
    analyze_parser.add_argument('--home-form', type=float, default=0.0, help='Home team form (-1 to 1)')
    analyze_parser.add_argument('--away-form', type=float, default=0.0, help='Away team form (-1 to 1)')
    analyze_parser.add_argument('--home-gd', type=int, default=0, help='Home team goal difference')
    analyze_parser.add_argument('--away-gd', type=int, default=0, help='Away team goal difference')
    analyze_parser.add_argument('--bankroll', type=float, default=BANKROLL, help='Current bankroll')
    analyze_parser.add_argument('--interactive', action='store_true', help='Interactive mode to place bet')
    
    # Bet command
    bet_parser = subparsers.add_parser('bet', help='Place a bet manually')
    bet_parser.add_argument('home_team', help='Home team name')
    bet_parser.add_argument('away_team', help='Away team name')
    bet_parser.add_argument('bet_type', choices=['home', 'draw', 'away'], help='Bet type')
    bet_parser.add_argument('odds', type=float, help='Decimal odds')
    bet_parser.add_argument('stake', type=float, help='Bet amount')
    bet_parser.add_argument('true_prob', type=float, help='True probability (%)')
    bet_parser.add_argument('market_prob', type=float, help='Market probability (%)')
    bet_parser.add_argument('--match-date', help='Match date (YYYY-MM-DD)')
    bet_parser.add_argument('--bankroll', type=float, default=BANKROLL, help='Current bankroll')
    
    # Settle command
    settle_parser = subparsers.add_parser('settle', help='Settle a bet')
    settle_parser.add_argument('bet_id', type=int, help='Bet ID')
    settle_parser.add_argument('result', choices=['win', 'loss', 'push'], help='Bet result')
    
    # Update ratings command
    update_parser = subparsers.add_parser('update-ratings', help='Update team ratings from match result')
    update_parser.add_argument('home_team', help='Home team name')
    update_parser.add_argument('away_team', help='Away team name')
    update_parser.add_argument('home_score', type=int, help='Home team score')
    update_parser.add_argument('away_score', type=int, help='Away team score')
    update_parser.add_argument('--match-date', help='Match date (YYYY-MM-DD)')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show betting statistics')
    
    # List bets command
    list_parser = subparsers.add_parser('list-bets', help='List bets')
    list_parser.add_argument('--pending', action='store_true', help='Show only pending bets')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Route to appropriate command handler
    if args.command == 'analyze':
        analyze_command(args)
    elif args.command == 'bet':
        bet_command(args)
    elif args.command == 'settle':
        settle_command(args)
    elif args.command == 'update-ratings':
        update_ratings_command(args)
    elif args.command == 'stats':
        stats_command(args)
    elif args.command == 'list-bets':
        list_bets_command(args)


if __name__ == '__main__':
    main()
