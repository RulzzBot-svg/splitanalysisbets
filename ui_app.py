"""
Streamlit UI for NBA SplitAnalysisBets (no more typing CLI commands)

Features:
- Team picker loaded from NBA DB (dropdown)
- Decimal odds mode and Splits (cents) mode (2-way)
- Analyze game (shows Elo, market probs, true probs, edge, recommendation)
- One-click log recommended bet (auto-fills nba-bet fields)
- List bets + settle (win/loss)
- Stats summary

NOTE:
- This file assumes your NBA code uses a sqlite DB (e.g., nba_bets.db) and has tables for:
  - team_ratings(team_name, elo_rating)
  - bets( ... )  (whatever your CLI uses)
If your table names differ, adjust the SQL in 2 spots: get_teams(), list_bets().
"""

import sqlite3
from datetime import date

import streamlit as st

# --- Import your NBA bot (adjust module paths if yours differ) ---
# These names are inferred from your CLI command set.
from nba_bot.bot import NBABettingBot  # your NBA bot wrapper
from nba_bot.probability import (
    decimal_odds_to_probability,
    cents_to_probability,
    remove_vig_two_way,
)
from nba_bot.betting import calculate_bet_size  # if you have it


DB_PATH = "nba_bets.db"


# -----------------------------
# DB helpers
# -----------------------------
def get_teams():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT team_name FROM team_ratings ORDER BY team_name")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


def insert_bet(
    home_team: str,
    away_team: str,
    bet_type: str,  # "home" or "away"
    odds: float,
    stake: float,
    true_prob: float,   # %
    market_prob: float, # %
    match_date: str,
    bankroll: float | None,
):
    """
    Try to save using the same DB your CLI uses.
    If your schema differs, update this insert statement to match.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Try a flexible insert. If your DB schema differs, Streamlit will show the error.
    cur.execute(
        """
        INSERT INTO bets (
            match_date, home_team, away_team, bet_type,
            odds, stake, true_prob, market_prob, bankroll, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (match_date, home_team, away_team, bet_type, odds, stake, true_prob, market_prob, bankroll),
    )

    conn.commit()
    conn.close()


def list_bets(limit=200):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # If your table/columns differ, adjust here.
    cur.execute(
        """
        SELECT
          id,
          match_date,
          home_team,
          away_team,
          bet_type,
          odds,
          stake,
          true_prob,
          market_prob,
          status,
          result,
          pnl
        FROM bets
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def settle_bet(bet_id: int, result: str):
    """
    Minimal settle: mark result and compute pnl based on odds/stake.
    If your CLI has more complex logic, align this with it.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT odds, stake FROM bets WHERE id = ?", (bet_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError("Bet not found")

    odds, stake = float(row[0]), float(row[1])

    if result.lower() == "win":
        pnl = (odds * stake) - stake
        status = "settled"
    else:
        pnl = -stake
        status = "settled"

    cur.execute(
        """
        UPDATE bets
        SET status = ?, result = ?, pnl = ?, settled_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (status, result.lower(), pnl, bet_id),
    )

    conn.commit()
    conn.close()


# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="NBA SplitAnalysisBets", layout="wide")
st.title("NBA SplitAnalysisBets — Streamlit UI")

bot = NBABettingBot()

teams = get_teams()
if not teams:
    st.warning("No teams found in DB. Import ratings first (nba-import-ratings) or update ratings.")
    st.stop()

tabs = st.tabs(["Analyze", "Bets", "Stats"])

# Keep last analysis in session to allow one-click logging
if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = None

with tabs[0]:
    st.subheader("Single Game Analyzer (NBA 2-way)")

    col1, col2 = st.columns(2)
    home_team = col1.selectbox("Home team", options=teams, index=0)
    away_team = col2.selectbox("Away team", options=[t for t in teams if t != home_team], index=0)

    mode = st.radio("Input mode", options=["Decimal odds", "Splits (cents)"], horizontal=True)

    if mode == "Decimal odds":
        c1, c2 = st.columns(2)
        home_odds = c1.number_input("Home odds (decimal)", value=2.44, min_value=1.01, format="%.3f")
        away_odds = c2.number_input("Away odds (decimal)", value=1.67, min_value=1.01, format="%.3f")
        market_home_raw = decimal_odds_to_probability(home_odds) * 100.0
        market_away_raw = decimal_odds_to_probability(away_odds) * 100.0
    else:
        st.info("Enter market splits in cents (example: 41 / 60). Doesn’t have to sum to 100.")
        c1, c2 = st.columns(2)
        home_cents = c1.number_input("Home (cents)", value=41, min_value=0, step=1)
        away_cents = c2.number_input("Away (cents)", value=60, min_value=0, step=1)
        market_home_raw = cents_to_probability(home_cents) * 100.0
        market_away_raw = cents_to_probability(away_cents) * 100.0

        # Also compute implied decimal odds from cents for display
        home_odds = (1.0 / max(cents_to_probability(home_cents), 1e-9))
        away_odds = (1.0 / max(cents_to_probability(away_cents), 1e-9))

    bank = st.number_input("Bankroll", value=1000.0, min_value=1.0, step=50.0)
    match_date = st.date_input("Match date", value=date.today()).isoformat()

    if st.button("Analyze game", type="primary"):
        # Remove vig (normalize to 100%)
        market_home, market_away = remove_vig_two_way(market_home_raw, market_away_raw)

        # Ask model for true probs
        analysis = bot.analyze_game_manual(
            home_team=home_team,
            away_team=away_team,
            home_odds=float(home_odds),
            away_odds=float(away_odds),
        )
        # Expected keys:
        # analysis = {
        #  "home_elo":..., "away_elo":...,
        #  "market_home":..., "market_away":...,
        #  "true_home":..., "true_away":...,
        #  "edge_home":..., "edge_away":...,
        #  "recommendation": {"bet_type":"home/away", "odds":..., "stake":..., "true_prob":..., "market_prob":...} or None
        # }

        # If your analyze_game_manual already computes vig-removed market probs, we keep those.
        st.session_state.last_analysis = analysis

    analysis = st.session_state.last_analysis
    if analysis:
        left, right = st.columns([2, 1])

        with left:
            st.markdown("### Results")

            st.write("**Team Elo Ratings:**")
            st.write(f"- {home_team}: {analysis['home_elo']}")
            st.write(f"- {away_team}: {analysis['away_elo']}")

            st.write("**Market Probabilities (vig removed):**")
            st.write(f"- Home: {analysis['market_home']:.2f}%")
            st.write(f"- Away: {analysis['market_away']:.2f}%")

            st.write("**Model (True) Probabilities:**")
            st.write(f"- Home: {analysis['true_home']:.2f}%")
            st.write(f"- Away: {analysis['true_away']:.2f}%")

            st.write("**Edges (True - Market):**")
            st.write(f"- Home: {analysis['edge_home']:+.2f}%")
            st.write(f"- Away: {analysis['edge_away']:+.2f}%")

        with right:
            st.markdown("### Recommendation")

            rec = analysis.get("recommendation")
            if not rec:
                st.info("No bet recommended (filters not met).")
            else:
                st.success(f"Bet: **{rec['bet_type'].upper()}**")
                st.write(f"**Odds:** {rec['odds']:.3f}")
                st.write(f"**Recommended Stake:** ${rec['stake']:.2f}")
                st.write(f"**True Prob:** {rec['true_prob']:.2f}%")
                st.write(f"**Market Prob:** {rec['market_prob']:.2f}%")
                st.write(f"**Edge:** {rec['edge']:+.2f}%")

                # One-click log
                if st.button("Log this bet to DB", type="primary"):
                    try:
                        insert_bet(
                            home_team=home_team,
                            away_team=away_team,
                            bet_type=rec["bet_type"].lower(),  # "home" or "away"
                            odds=float(rec["odds"]),
                            stake=float(rec["stake"]),
                            true_prob=float(rec["true_prob"]),
                            market_prob=float(rec["market_prob"]),
                            match_date=match_date,
                            bankroll=float(bank),
                        )
                        st.success("Saved bet ✅")
                    except Exception as e:
                        st.error(f"Could not save bet. DB schema mismatch? Error: {e}")

with tabs[1]:
    st.subheader("Recorded Bets")

    rows = []
    try:
        rows = list_bets(limit=200)
    except Exception as e:
        st.error(f"Could not load bets. DB schema mismatch? Error: {e}")

    if rows:
        st.dataframe(
            rows,
            use_container_width=True,
            column_config={
                0: "id",
                1: "match_date",
                2: "home_team",
                3: "away_team",
                4: "bet_type",
                5: "odds",
                6: "stake",
                7: "true_prob",
                8: "market_prob",
                9: "status",
                10: "result",
                11: "pnl",
            },
        )

        st.markdown("### Settle a bet")
        c1, c2, c3 = st.columns([2, 2, 3])
        bet_id = c1.number_input("Bet ID", min_value=1, step=1, value=1)
        result = c2.selectbox("Result", options=["win", "loss"])
        if c3.button("Settle", type="primary"):
            try:
                settle_bet(int(bet_id), result)
                st.success("Bet settled ✅ (refresh the table)")
            except Exception as e:
                st.error(str(e))
    else:
        st.info("No bets recorded yet. Use Analyze → Log this bet.")

with tabs[2]:
    st.subheader("Stats")

    # Minimal stats from DB
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM bets")
        total = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM bets WHERE status = 'settled'")
        settled = cur.fetchone()[0]

        cur.execute("SELECT COALESCE(SUM(pnl), 0) FROM bets WHERE status = 'settled'")
        pnl = float(cur.fetchone()[0])

        cur.execute("SELECT COUNT(*) FROM bets WHERE status = 'settled' AND pnl > 0")
        wins = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM bets WHERE status = 'settled' AND pnl <= 0")
        losses = cur.fetchone()[0]

        conn.close()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total bets", total)
        c2.metric("Settled", settled)
        c3.metric("Wins / Losses", f"{wins} / {losses}")
        c4.metric("Net PnL", f"{pnl:.2f}")

    except Exception as e:
        st.error(f"Could not compute stats. Error: {e}")