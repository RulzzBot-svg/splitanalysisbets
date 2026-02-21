#!/usr/bin/env python3
"""
Command-line interface for the NBA betting bot.

Commands:
  nba-analyze      Analyse a game and get a betting recommendation
  nba-bet          Record a bet manually
  nba-settle       Settle a recorded bet
  nba-update-ratings  Update team Elo ratings from a game result
  nba-stats        Show betting statistics
  nba-list-bets    List recorded bets
  nba-import-ratings  Import Elo ratings from a CSV file
"""
import argparse
import sys
from nba_bot.bot import NBABettingBot
from nba_bot.config import BANKROLL, EDGE_THRESHOLD
from nba_bot.model import normalize_team_name, is_current_nba_team


# ---------------------------------------------------------------------------
# Printing helpers
# ---------------------------------------------------------------------------

def print_analysis(analysis: dict):
    """Print NBA game analysis in a readable format."""
    print(f"\n{'=' * 70}")
    print(f"GAME ANALYSIS: {analysis['home_team']} vs {analysis['away_team']}")
    print(f"{'=' * 70}")

    print("\nTeam Elo Ratings:")
    print(f"  {analysis['home_team']}: {analysis['team_ratings']['home']:.0f}")
    print(f"  {analysis['away_team']}: {analysis['team_ratings']['away']:.0f}")

    debug_info = analysis.get('debug')
    if debug_info:
        print("\nDebug:")
        print(f"  home_team (normalized): {normalize_team_name(analysis['home_team'])}")
        print(f"  away_team (normalized): {normalize_team_name(analysis['away_team'])}")
        print(f"  home_elo_raw: {debug_info['home_rating']:.2f}")
        print(f"  away_elo_raw: {debug_info['away_rating']:.2f}")
        print(f"  elo_diff (home-away, adjusted): {debug_info['elo_diff']:.2f}")
        print(f"  p_home_raw (pre-calibration): {debug_info['home_win_p_raw'] * 100.0:.2f}%")

    print("\nMarket Probabilities (vig removed):")
    print(f"  Home: {analysis['market_probabilities']['home']:.2f}%")
    print(f"  Away: {analysis['market_probabilities']['away']:.2f}%")

    print("\nModel (True) Probabilities:")
    print(f"  Home: {analysis['true_probabilities']['home']:.2f}%")
    print(f"  Away: {analysis['true_probabilities']['away']:.2f}%")

    print("\nEdges (True - Market):")
    print(f"  Home: {analysis['edges']['home']:+.2f}%")
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
        print(f"\nNo bet recommended (does not meet filters: "
              f"model_prob >= 62%, edge >= {EDGE_THRESHOLD}%)")

    print()


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def analyze_command(args):
    """Handle nba-analyze command."""
    bot = NBABettingBot(bankroll=args.bankroll)

    # Allow overriding Elo ratings for one-off analysis
    if getattr(args, 'home_elo', None) is not None:
        try:
            bot.team_ratings.update_rating(args.home_team, float(args.home_elo))
            bot.database.save_team_rating(args.home_team, float(args.home_elo))
        except (ValueError, TypeError) as e:
            print(f"Warning: could not set home Elo: {e}")
    if getattr(args, 'away_elo', None) is not None:
        try:
            bot.team_ratings.update_rating(args.away_team, float(args.away_elo))
            bot.database.save_team_rating(args.away_team, float(args.away_elo))
        except (ValueError, TypeError) as e:
            print(f"Warning: could not set away Elo: {e}")

    analysis = bot.analyze_game(
        home_team=args.home_team,
        away_team=args.away_team,
        home_ml=getattr(args, 'home_ml', None),
        away_ml=getattr(args, 'away_ml', None),
        home_odds=getattr(args, 'home_odds', None),
        away_odds=getattr(args, 'away_odds', None),
        rest_diff=args.rest_diff,
        home_b2b=args.home_b2b,
        away_b2b=args.away_b2b,
        home_star_out=args.home_star_out,
        away_star_out=args.away_star_out,
        debug=args.debug,
    )

    print_analysis(analysis)

    if analysis['recommendation'] and args.interactive:
        response = input("\nPlace this bet? (yes/no): ").strip().lower()
        if response in ('yes', 'y'):
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
            print(f"\n✓ Bet placed! Bet ID: {bet_id}")
            print(f"  New bankroll: ${bot.bankroll:.2f}")


def bet_command(args):
    """Handle nba-bet command."""
    bot = NBABettingBot(bankroll=args.bankroll)

    bet_id = bot.place_bet(
        home_team=args.home_team,
        away_team=args.away_team,
        bet_type=args.bet_type,
        odds=args.odds,
        stake=args.stake,
        true_probability=args.true_prob,
        market_probability=args.market_prob,
        edge=args.true_prob - args.market_prob,
        match_date=args.match_date,
    )

    print(f"✓ Bet placed! Bet ID: {bet_id}")
    print(f"  New bankroll: ${bot.bankroll:.2f}")


def settle_command(args):
    """Handle nba-settle command."""
    bot = NBABettingBot()
    bot.settle_bet(args.bet_id, args.result)
    print(f"✓ Bet {args.bet_id} settled as {args.result}")
    print(f"  Current bankroll: ${bot.bankroll:.2f}")


def update_ratings_command(args):
    """Handle nba-update-ratings command."""
    bot = NBABettingBot()
    bot.update_ratings_from_result(
        home_team=args.home_team,
        away_team=args.away_team,
        home_score=args.home_score,
        away_score=args.away_score,
        game_date=args.game_date,
        season=args.season,
    )
    print(f"✓ Ratings updated for {args.home_team} vs {args.away_team}")
    print(f"  {args.home_team}: {bot.team_ratings.get_rating(args.home_team):.0f}")
    print(f"  {args.away_team}: {bot.team_ratings.get_rating(args.away_team):.0f}")


def stats_command(args):
    """Handle nba-stats command."""
    bot = NBABettingBot()
    stats = bot.get_statistics()

    print(f"\n{'=' * 70}")
    print("NBA BETTING STATISTICS")
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
    """Handle nba-list-bets command."""
    bot = NBABettingBot()

    if args.pending:
        bets = bot.get_pending_bets()
        header = f"PENDING NBA BETS ({len(bets)})"
    else:
        bets = bot.get_all_bets()
        header = f"ALL NBA BETS ({len(bets)})"

    print(f"\n{'=' * 70}")
    print(header)
    print(f"{'=' * 70}")

    if not bets:
        print("No bets found.")
        return

    for bet in bets:
        print(f"\nBet ID: {bet['id']}")
        print(f"  Game:  {bet['home_team']} vs {bet['away_team']}")
        print(f"  Type:  {bet['bet_type']}")
        print(f"  Odds:  {bet['odds']}")
        print(f"  Stake: ${bet['stake']:.2f}")
        print(f"  Edge:  {bet['edge']:+.2f}%")
        if bet['result']:
            print(f"  Result: {bet['result']}")
            print(f"  P/L:    ${bet['profit_loss']:+.2f}")
    print()


def import_ratings_command(args):
    """Handle nba-import-ratings command — import Elo ratings from CSV."""
    import csv
    bot = NBABettingBot()

    try:
        with open(args.csv_path, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            count = 0
            for row in reader:
                team = (row.get('team_name') or row.get('team') or '').strip()
                elo = (row.get('elo') or row.get('rating') or '').strip()
                if not team or not elo:
                    continue
                if not is_current_nba_team(team):
                    continue
                try:
                    elo_val = float(elo)
                except ValueError:
                    continue
                bot.team_ratings.update_rating(team, elo_val)
                bot.database.save_team_rating(team, elo_val)
                count += 1
        print(f"Imported {count} ratings from {args.csv_path}")
    except FileNotFoundError:
        print(f"File not found: {args.csv_path}")
    except Exception as e:
        print(f"Error importing ratings: {e}")


# ---------------------------------------------------------------------------
# CLI definition
# ---------------------------------------------------------------------------

def main():
    """NBA betting bot CLI entry point."""
    parser = argparse.ArgumentParser(
        description='NBA Betting Decision Bot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # ---- nba-analyze -------------------------------------------------------
    analyze_parser = subparsers.add_parser('nba-analyze', help='Analyse an NBA game')
    analyze_parser.add_argument('home_team', help='Home team name')
    analyze_parser.add_argument('away_team', help='Away team name')

    odds_group = analyze_parser.add_mutually_exclusive_group(required=True)
    odds_group.add_argument('--ml', nargs=2, type=float, metavar=('HOME_ML', 'AWAY_ML'),
                            help='American moneyline odds (e.g. --ml -150 +130)')
    odds_group.add_argument('--decimal', nargs=2, type=float,
                            metavar=('HOME_ODDS', 'AWAY_ODDS'),
                            help='Decimal odds (e.g. --decimal 1.67 2.10)')

    analyze_parser.add_argument('--rest-diff', type=int, default=0,
                                help='Extra rest days home team has over away (can be negative)')
    analyze_parser.add_argument('--home-b2b', action='store_true',
                                help='Home team is on a back-to-back')
    analyze_parser.add_argument('--away-b2b', action='store_true',
                                help='Away team is on a back-to-back')
    analyze_parser.add_argument('--home-star-out', action='store_true',
                                help='Star player out for home team')
    analyze_parser.add_argument('--away-star-out', action='store_true',
                                help='Star player out for away team')
    analyze_parser.add_argument('--home-elo', type=float,
                                help='Override home team Elo rating for this analysis')
    analyze_parser.add_argument('--away-elo', type=float,
                                help='Override away team Elo rating for this analysis')
    analyze_parser.add_argument('--bankroll', type=float, default=BANKROLL,
                                help='Current bankroll')
    analyze_parser.add_argument('--interactive', action='store_true',
                                help='Prompt to place bet after analysis')
    analyze_parser.add_argument('--debug', action='store_true',
                                help='Print normalized team keys, Elo diff, and raw model probability')

    # ---- nba-bet -----------------------------------------------------------
    bet_parser = subparsers.add_parser('nba-bet', help='Record a bet manually')
    bet_parser.add_argument('home_team', help='Home team name')
    bet_parser.add_argument('away_team', help='Away team name')
    bet_parser.add_argument('bet_type', choices=['home', 'away'], help='Bet type')
    bet_parser.add_argument('odds', type=float, help='Decimal odds')
    bet_parser.add_argument('stake', type=float, help='Bet amount')
    bet_parser.add_argument('true_prob', type=float, help='True probability (%%)')
    bet_parser.add_argument('market_prob', type=float, help='Market probability (%%)')
    bet_parser.add_argument('--match-date', help='Game date (YYYY-MM-DD)')
    bet_parser.add_argument('--bankroll', type=float, default=BANKROLL,
                            help='Current bankroll')

    # ---- nba-settle --------------------------------------------------------
    settle_parser = subparsers.add_parser('nba-settle', help='Settle a recorded bet')
    settle_parser.add_argument('bet_id', type=int, help='Bet ID')
    settle_parser.add_argument('result', choices=['win', 'loss', 'push'], help='Bet result')

    # ---- nba-update-ratings ------------------------------------------------
    update_parser = subparsers.add_parser('nba-update-ratings',
                                          help='Update Elo ratings from a game result')
    update_parser.add_argument('home_team', help='Home team name')
    update_parser.add_argument('away_team', help='Away team name')
    update_parser.add_argument('home_score', type=int, help='Home team score')
    update_parser.add_argument('away_score', type=int, help='Away team score')
    update_parser.add_argument('--game-date', help='Game date (YYYY-MM-DD)')
    update_parser.add_argument('--season', help='Season label (e.g. 2024-25)')

    # ---- nba-stats ---------------------------------------------------------
    subparsers.add_parser('nba-stats', help='Show betting statistics')

    # ---- nba-list-bets -----------------------------------------------------
    list_parser = subparsers.add_parser('nba-list-bets', help='List recorded bets')
    list_parser.add_argument('--pending', action='store_true',
                             help='Show only pending (unsettled) bets')

    # ---- nba-import-ratings ------------------------------------------------
    import_parser = subparsers.add_parser('nba-import-ratings',
                                          help='Import Elo ratings from CSV')
    import_parser.add_argument('csv_path',
                               help='Path to CSV file with columns: team_name, elo')

    # ---- Parse & dispatch --------------------------------------------------
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'nba-analyze':
        # Unpack odds group
        if args.ml:
            args.home_ml, args.away_ml = args.ml
            args.home_odds = args.away_odds = None
        else:
            args.home_odds, args.away_odds = args.decimal
            args.home_ml = args.away_ml = None
        analyze_command(args)
    elif args.command == 'nba-bet':
        bet_command(args)
    elif args.command == 'nba-settle':
        settle_command(args)
    elif args.command == 'nba-update-ratings':
        update_ratings_command(args)
    elif args.command == 'nba-stats':
        stats_command(args)
    elif args.command == 'nba-list-bets':
        list_bets_command(args)
    elif args.command == 'nba-import-ratings':
        import_ratings_command(args)


if __name__ == '__main__':
    main()
