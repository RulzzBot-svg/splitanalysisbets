#!/usr/bin/env python3
"""
Command-line interface for soccer betting bot
"""
import argparse
import sys
from soccer_bot.bot import SoccerBettingBot
from soccer_bot.config import BANKROLL, EDGE_THRESHOLD
from soccer_bot.api_client import FootballDataClient


def print_analysis(analysis):
    """Print match analysis in a readable format"""
    print(f"\n{'=' * 70}")
    print(f"MATCH ANALYSIS: {analysis['home_team']} vs {analysis['away_team']}")
    print(f"{'=' * 70}")
    
    print("\nTeam Elo Ratings:")
    print(f"  {analysis['home_team']}: {analysis['team_ratings']['home']}")
    print(f"  {analysis['away_team']}: {analysis['team_ratings']['away']}")
    
    print("\nMarket Probabilities (implied from odds):")
    print(f"  Home: {analysis['market_probabilities']['home']}percent")
    print(f"  Draw: {analysis['market_probabilities']['draw']}percent")
    print(f"  Away: {analysis['market_probabilities']['away']}percent")
    
    print("\nModel (True) Probabilities:")
    print(f"  Home: {analysis['true_probabilities']['home']}percent")
    print(f"  Draw: {analysis['true_probabilities']['draw']}percent")
    print(f"  Away: {analysis['true_probabilities']['away']}percent")
    
    print("\nEdges (True - Market):")
    print(f"  Home: {analysis['edges']['home']:+.2f}percent")
    print(f"  Draw: {analysis['edges']['draw']:+.2f}percent")
    print(f"  Away: {analysis['edges']['away']:+.2f}percent")
    
    if analysis['recommendation']:
        rec = analysis['recommendation']
        print(f"\n{'*' * 70}")
        print("BETTING RECOMMENDATION:")
        print(f"{'*' * 70}")
        print(f"  Bet Type: {rec['bet_type'].upper()}")
        print(f"  Odds: {rec['odds']}")
        print(f"  Recommended Stake: ${rec['stake']:.2f}")
        print(f"  Edge: {rec['edge']:+.2f}percent")
        print(f"  True Probability: {rec['true_probability']:.2f}percent")
        print(f"  Market Probability: {rec['market_probability']:.2f}percent")
        print(f"  Potential Return: ${rec['potential_return']:.2f}")
        print(f"  Potential Profit: ${rec['potential_profit']:.2f}")
        print(f"{'*' * 70}")
    else:
        print(f"\nNo bet recommended (edge below {EDGE_THRESHOLD}percent threshold)")
    
    print()


def analyze_command(args):
    """Handle analyze command"""
    bot = SoccerBettingBot(bankroll=args.bankroll)
    # Allow overriding Elo ratings for a one-off analysis; save to DB so future runs use them
    if getattr(args, 'home_elo', None) is not None:
        try:
            elo_val = float(args.home_elo)
            bot.team_ratings.update_rating(args.home_team, elo_val)
            bot.database.save_team_rating(args.home_team, elo_val)
        except Exception:
            pass
    if getattr(args, 'away_elo', None) is not None:
        try:
            elo_val = float(args.away_elo)
            bot.team_ratings.update_rating(args.away_team, elo_val)
            bot.database.save_team_rating(args.away_team, elo_val)
        except Exception:
            pass
    
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
    print(f"  Win Rate: {stats['win_rate']:.1f}percent")
    print(f"\nFinancials:")
    print(f"  Total Staked: ${stats['total_staked']:.2f}")
    print(f"  Total P/L: ${stats['total_profit_loss']:.2f}")
    print(f"  ROI: {stats['roi']:.2f}percent")
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
        print(f"  Edge: {bet['edge']:+.2f}percent")
        if bet['result']:
            print(f"  Result: {bet['result']}")
            print(f"  P/L: ${bet['profit_loss']:+.2f}")
    print()


def fetch_fixtures_command(args):
    """Handle fetch-fixtures command using FootballDataClient"""
    # Use provided API key if given, otherwise rely on config/env
    client = FootballDataClient(api_key=args.api_key) if args.api_key else FootballDataClient()

    matches = client.get_fixtures(competition_id=args.competition,
                                  date_from=args.date_from,
                                  date_to=args.date_to)

    print(f"\nFetched {len(matches)} fixtures")
    if not matches:
        return

    for m in matches:
        # Safe extraction from API response
        date = m.get('utcDate') or m.get('matchDate') or m.get('date')
        home = (m.get('homeTeam') or {}).get('name') if isinstance(m.get('homeTeam'), dict) else m.get('homeTeam')
        away = (m.get('awayTeam') or {}).get('name') if isinstance(m.get('awayTeam'), dict) else m.get('awayTeam')
        print(f"- {date}: {home} vs {away}")


def compute_ratings_command(args):
    """Compute Elo ratings from historical matches fetched from football-data.org"""
    from datetime import datetime
    bot = SoccerBettingBot()

    client = FootballDataClient(api_key=args.api_key) if args.api_key else FootballDataClient()
    # football-data.org limits period to 10 days per request; iterate windows
    from datetime import timedelta

    date_from = args.date_from
    date_to = args.date_to
    windows = []
    if date_from and date_to:
        try:
            start = datetime.fromisoformat(date_from)
            end = datetime.fromisoformat(date_to)
        except Exception:
            print('Invalid date format; use YYYY-MM-DD')
            return

        cur = start
        while cur <= end:
            window_end = min(end, cur + timedelta(days=9))
            windows.append((cur.date().isoformat(), window_end.date().isoformat()))
            cur = window_end + timedelta(days=1)
    else:
        # Single unbounded call (may still be rejected by API)
        windows.append((date_from, date_to))

    total_processed = 0
    for w_from, w_to in windows:
        matches = client.get_fixtures(competition_id=args.competition, date_from=w_from, date_to=w_to)

        # Filter and sort matches by date
        parsed = []
        for m in matches:
            date = m.get('utcDate') or m.get('matchDate') or m.get('date')
            try:
                dt = datetime.fromisoformat(date.replace('Z', '+00:00')) if date else None
            except Exception:
                dt = None
            parsed.append((dt, m))

        parsed.sort(key=lambda x: (x[0] is None, x[0]))

        processed = 0
        for dt, m in parsed:
            # Extract score
            score = m.get('score', {})
            full = score.get('fullTime', {}) if isinstance(score, dict) else {}
            home_score = full.get('home')
            away_score = full.get('away')

            # Skip matches without final score
            if home_score is None or away_score is None:
                continue

            home = (m.get('homeTeam') or {}).get('name') if isinstance(m.get('homeTeam'), dict) else m.get('homeTeam')
            away = (m.get('awayTeam') or {}).get('name') if isinstance(m.get('awayTeam'), dict) else m.get('awayTeam')

            if not home or not away:
                continue

            # Update ratings
            try:
                bot.team_ratings.update_ratings_after_match(home, away, int(home_score), int(away_score))
                # Persist ratings
                bot.database.save_team_rating(home, bot.team_ratings.get_rating(home))
                bot.database.save_team_rating(away, bot.team_ratings.get_rating(away))

                # Save match result
                match_date = dt.date().isoformat() if dt else None
                comp = (m.get('competition') or {}).get('name') if isinstance(m.get('competition'), dict) else args.competition
                bot.database.add_match_result(match_date, home, away, int(home_score), int(away_score), competition=comp)

                processed += 1
                total_processed += 1
            except Exception:
                continue

        print(f"Window {w_from} -> {w_to}: processed {processed} matches")

    print(f"Processed {total_processed} matches and updated Elo ratings")


def import_ratings_command(args):
    """Import Elo ratings from CSV file with columns: team_name,elo"""
    import csv
    bot = SoccerBettingBot()

    try:
        with open(args.csv_path, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            count = 0
            for row in reader:
                team = (row.get('team_name') or row.get('team') or '').strip()
                elo = (row.get('elo') or row.get('rating') or '').strip()
                if not team or not elo:
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


def compute_ratings_from_csv_command(args):
    """Compute Elo ratings from a CSV file or URL of historical matches."""
    import csv
    import tempfile
    import os
    from datetime import datetime
    import requests

    csv_path = args.csv_path
    if not csv_path and args.url:
        # download to temp file
        try:
            r = requests.get(args.url, timeout=30)
            r.raise_for_status()
            fd, tmp = tempfile.mkstemp(suffix='.csv')
            with os.fdopen(fd, 'wb') as fh:
                fh.write(r.content)
            csv_path = tmp
        except Exception as e:
            print(f"Error downloading CSV: {e}")
            return

    if not csv_path or not os.path.exists(csv_path):
        print('CSV path not provided or file not found')
        return

    bot = SoccerBettingBot()

    rows = []
    with open(csv_path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            # Extract required fields using provided column names
            date_s = row.get(args.date_col)
            home = row.get(args.home_col) or row.get('home')
            away = row.get(args.away_col) or row.get('away')
            hs = row.get(args.home_score_col) or row.get('FTHG') or row.get('home_score')
            as_ = row.get(args.away_score_col) or row.get('FTAG') or row.get('away_score')

            if not date_s or not home or not away or hs is None or as_ is None:
                continue

            # parse date
            try:
                dt = datetime.fromisoformat(date_s)
            except Exception:
                # try common formats
                try:
                    dt = datetime.strptime(date_s, '%d/%m/%Y')
                except Exception:
                    try:
                        dt = datetime.strptime(date_s, '%Y-%m-%d')
                    except Exception:
                        continue

            try:
                hs_i = int(hs)
                as_i = int(as_)
            except Exception:
                continue

            rows.append((dt, home.strip(), away.strip(), hs_i, as_i))

    if not rows:
        print('No valid match rows found in CSV')
        return

    rows.sort(key=lambda x: x[0])

    processed = 0
    for dt, home, away, hs_i, as_i in rows:
        try:
            bot.team_ratings.update_ratings_after_match(home, away, hs_i, as_i)
            bot.database.save_team_rating(home, bot.team_ratings.get_rating(home))
            bot.database.save_team_rating(away, bot.team_ratings.get_rating(away))
            bot.database.add_match_result(dt.date().isoformat(), home, away, hs_i, as_i)
            processed += 1
        except Exception:
            continue

    print(f"Processed {processed} matches from CSV and updated Elo ratings")


def compute_ratings_from_football_data_co_uk(args):
    """Download season CSVs from football-data.co.uk (mmz4281) and compute Elo."""
    import tempfile
    import os
    import requests
    from datetime import datetime

    league = args.league
    start = args.start_year
    end = args.end_year
    if start > end:
        print('start-year must be <= end-year')
        return

    bot = SoccerBettingBot()
    total = 0

    for year in range(start, end + 1):
        # football-data.co.uk season code: YYZZ where YY = start_year%100, ZZ = (start_year+1)%100
        s1 = str(year % 100).zfill(2)
        s2 = str((year + 1) % 100).zfill(2)
        season_code = f"{s1}{s2}"
        url = f"https://www.football-data.co.uk/mmz4281/{season_code}/{league}.csv"

        print(f"Downloading {url}")
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            continue

        # Save to temp file and reuse CSV processor logic
        fd, tmp = tempfile.mkstemp(suffix='.csv')
        with os.fdopen(fd, 'wb') as fh:
            fh.write(r.content)

        # Reuse compute_ratings_from_csv_command-like parsing
        # We'll parse common columns used by football-data.co.uk: Date, HomeTeam, AwayTeam, FTHG, FTAG
        import csv
        rows = []
        with open(tmp, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                date_s = row.get('Date') or row.get('date')
                home = row.get('HomeTeam') or row.get('home_team')
                away = row.get('AwayTeam') or row.get('away_team')
                hs = row.get('FTHG') or row.get('HomeGoals') or row.get('home_score')
                as_ = row.get('FTAG') or row.get('AwayGoals') or row.get('away_score')

                if not date_s or not home or not away or hs is None or as_ is None:
                    continue

                # parse date formats like DD/MM/YY or DD/MM/YYYY
                dt = None
                for fmt in ('%d/%m/%Y', '%d/%m/%y', '%Y-%m-%d'):
                    try:
                        dt = datetime.strptime(date_s, fmt)
                        break
                    except Exception:
                        continue
                if not dt:
                    continue

                try:
                    hs_i = int(hs)
                    as_i = int(as_)
                except Exception:
                    continue

                rows.append((dt, home.strip(), away.strip(), hs_i, as_i))

        os.remove(tmp)

        if not rows:
            print(f'No matches found in {url}')
            continue

        rows.sort(key=lambda x: x[0])
        processed = 0
        for dt, home, away, hs_i, as_i in rows:
            try:
                bot.team_ratings.update_ratings_after_match(home, away, hs_i, as_i)
                bot.database.save_team_rating(home, bot.team_ratings.get_rating(home))
                bot.database.save_team_rating(away, bot.team_ratings.get_rating(away))
                bot.database.add_match_result(dt.date().isoformat(), home, away, hs_i, as_i, competition=league)
                processed += 1
                total += 1
            except Exception:
                continue

        print(f"Season {year}-{year+1}: processed {processed} matches")

    print(f"Total processed across seasons: {total}")


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
    analyze_parser.add_argument('--home-elo', type=float, help='Override home team Elo rating for this analysis')
    analyze_parser.add_argument('--away-elo', type=float, help='Override away team Elo rating for this analysis')
    analyze_parser.add_argument('--interactive', action='store_true', help='Interactive mode to place bet')
    
    # Bet command
    bet_parser = subparsers.add_parser('bet', help='Place a bet manually')
    bet_parser.add_argument('home_team', help='Home team name')
    bet_parser.add_argument('away_team', help='Away team name')
    bet_parser.add_argument('bet_type', choices=['home', 'draw', 'away'], help='Bet type')
    bet_parser.add_argument('odds', type=float, help='Decimal odds')
    bet_parser.add_argument('stake', type=float, help='Bet amount')
    bet_parser.add_argument('true_prob', type=float, help='True probability (percent)')
    bet_parser.add_argument('market_prob', type=float, help='Market probability (percent)')
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

    # Fetch fixtures command
    fetch_parser = subparsers.add_parser('fetch-fixtures', help='Fetch fixtures from football-data.org')
    fetch_parser.add_argument('--competition', help='Competition ID (e.g., PL)')
    fetch_parser.add_argument('--date-from', help='Start date (YYYY-MM-DD)')
    fetch_parser.add_argument('--date-to', help='End date (YYYY-MM-DD)')
    fetch_parser.add_argument('--api-key', help='football-data.org API key (optional)')
    
    # Import ratings command
    import_parser = subparsers.add_parser('import-ratings', help='Import Elo ratings from CSV')
    import_parser.add_argument('csv_path', help='Path to CSV file with columns team_name,elo')
    
    # Compute ratings command
    compute_parser = subparsers.add_parser('compute-ratings', help='Compute Elo from historical matches via football-data.org')
    compute_parser.add_argument('--competition', help='Competition ID (e.g., PL)')
    compute_parser.add_argument('--date-from', help='Start date (YYYY-MM-DD)')
    compute_parser.add_argument('--date-to', help='End date (YYYY-MM-DD)')
    compute_parser.add_argument('--api-key', help='football-data.org API key (optional)')

    # Compute ratings from CSV (local file or URL)
    csv_compute = subparsers.add_parser('compute-ratings-csv', help='Compute Elo from a CSV of historical matches')
    csv_compute.add_argument('--csv-path', help='Path to local CSV file with match results')
    csv_compute.add_argument('--url', help='URL to download CSV from (optional)')
    csv_compute.add_argument('--date-col', default='date', help='CSV column name for match date (default: date)')
    csv_compute.add_argument('--home-col', default='home_team', help='CSV column name for home team (default: home_team)')
    csv_compute.add_argument('--away-col', default='away_team', help='CSV column name for away team (default: away_team)')
    csv_compute.add_argument('--home-score-col', default='home_score', help='CSV column name for home score (default: home_score)')
    csv_compute.add_argument('--away-score-col', default='away_score', help='CSV column name for away score (default: away_score)')
    
    # football-data.co.uk quick importer
    fd_parser = subparsers.add_parser('compute-ratings-footballdata', help='Download seasons from football-data.co.uk and compute Elo')
    fd_parser.add_argument('--league', default='E0', help='League code used by football-data.co.uk (default E0 = Premier League)')
    fd_parser.add_argument('--start-year', type=int, required=True, help='Start season year (e.g., 2019 for 2019-20)')
    fd_parser.add_argument('--end-year', type=int, required=True, help='End season year (e.g., 2021 for 2021-22)')
    
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
    elif args.command == 'fetch-fixtures':
        fetch_fixtures_command(args)
    elif args.command == 'import-ratings':
        import_ratings_command(args)
    elif args.command == 'compute-ratings':
        compute_ratings_command(args)
    elif args.command == 'compute-ratings-csv':
        compute_ratings_from_csv_command(args)
    elif args.command == 'compute-ratings-footballdata':
        compute_ratings_from_football_data_co_uk(args)
    elif args.command == 'import-ratings':
        import_ratings_command(args)


if __name__ == '__main__':
    main()
