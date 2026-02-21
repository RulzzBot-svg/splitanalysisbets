#!/usr/bin/env python3
r"""
Batch-insert bets into the NBABettingBot.
Usage:
  # Create .env file from .env.example with your NBA_API_KEY
  python .\scripts\insert_bets.py
"""
from nba_bot.bot import NBABettingBot

# Default stake per bet
DEFAULT_STAKE = 100.0

# List of bets: (home_team, away_team, implied_pct_home, implied_pct_away, datetime_str)
bets = [
    ("ORL", "PHX", 46, 56, "2026-02-21T14:00"),
    ("PHI", "NOP", 61, 40, "2026-02-21T16:00"),
    ("SAC", "SAS", 8, 93, "2026-02-21T17:00"),
    ("DET", "CHI", 83, 18, "2026-02-21T17:00"),
    ("MEM", "MIA", 18, 83, "2026-02-21T17:00"),
    ("HOU", "NYK", 41, 60, "2026-02-21T17:30"),
    ("CLE", "OKC", 50, 53, "2026-02-22T10:00"),
]

def implied_to_decimal(pct):
    """Convert implied probability % to decimal odds."""
    p = float(pct) / 100.0
    if p <= 0:
        return 999.0
    return round(1.0 / p, 3)

def main():
    bot = NBABettingBot()
    created_ids = []
    
    print(f"\n{'=' * 70}")
    print(f"Inserting {len(bets)} bets with ${DEFAULT_STAKE:.2f} stake each")
    print(f"{'=' * 70}\n")
    
    for home, away, hp, ap, dt in bets:
        # Pick side with higher implied probability
        if hp >= ap:
            bet_type = "home"
            true_prob = hp
            market_prob = ap
            odds = implied_to_decimal(hp)
        else:
            bet_type = "away"
            true_prob = ap
            market_prob = hp
            odds = implied_to_decimal(ap)

        bet_id = bot.place_bet(
            home_team=home,
            away_team=away,
            bet_type=bet_type,
            odds=odds,
            stake=DEFAULT_STAKE,
            true_probability=true_prob,
            market_probability=market_prob,
            edge=true_prob - market_prob,
            match_date=dt,
        )
        
        print(f"✓ Bet {bet_id}: {home} vs {away} — {bet_type.upper()} @ {odds} | Stake: ${DEFAULT_STAKE:.2f} | Edge: {true_prob - market_prob:+.1f}%")
        created_ids.append(bet_id)
    
    print(f"\n{'=' * 70}")
    print(f"Successfully created {len(created_ids)} bets")
    print(f"Bet IDs: {created_ids}")
    print(f"Current bankroll: ${bot.bankroll:.2f}")
    print(f"{'=' * 70}\n")

if __name__ == "__main__":
    main()
