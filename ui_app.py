"""
Streamlit UI for SplitAnalysisBets

Features:
- Team picker loaded from DB (dropdown)
- Decimal odds mode and Splits (cents) mode
- Daily board: fetch tomorrow's fixtures and rank edges (given splits)
- Quick Elo update from recent results
"""

import io
import sqlite3
from datetime import date, timedelta

import streamlit as st

from soccer_bot.bot import SoccerBettingBot
from soccer_bot.probability import implied_probability_to_odds
from soccer_bot.betting import calculate_bet_size
from soccer_bot.api_client import FootballDataClient
from soccer_bot.config import FOOTBALL_DATA_API_KEY


DB_PATH = "soccer_bets.db"


def get_teams():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT team_name FROM team_ratings ORDER BY team_name")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


st.set_page_config(page_title="SplitAnalysisBets UI", layout="wide")
st.title("SplitAnalysisBets — Streamlit UI")

bot = SoccerBettingBot()

teams = get_teams()
if not teams:
    st.warning("No teams found in DB. Run `compute-ratings-footballdata` or import CSV ratings first.")

# Layout
left, right = st.columns([2, 1])

with left:
    st.subheader("Single Match Analyzer")
    col1, col2 = st.columns(2)
    home_team = col1.selectbox("Home team", options=teams)
    away_team = col2.selectbox("Away team", options=[t for t in teams if t != home_team])

    mode = st.radio("Input mode", options=["Decimal odds", "Splits (cents)"])

    if mode == "Decimal odds":
        c1, c2, c3 = st.columns(3)
        home_odds = c1.number_input("Home odds (decimal)", value=2.10, min_value=1.01, format="%.2f")
        draw_odds = c2.number_input("Draw odds (decimal)", value=3.50, min_value=1.01, format="%.2f")
        away_odds = c3.number_input("Away odds (decimal)", value=3.60, min_value=1.01, format="%.2f")
        use_splits = False
    else:
        st.info("Enter market splits in cents (must sum to ~100). Example: 67 / 18 / 15")
        s1, s2, s3 = st.columns(3)
        home_split = s1.number_input("Home (cents)", value=67, min_value=0)
        draw_split = s2.number_input("Draw (cents)", value=18, min_value=0)
        away_split = s3.number_input("Away (cents)", value=15, min_value=0)
        use_splits = True

    bank = st.number_input("Bankroll", value=1000.0, min_value=1.0)

    if st.button("Analyze match"):
        # Get Elo ratings
        home_elo = bot.team_ratings.get_rating(home_team)
        away_elo = bot.team_ratings.get_rating(away_team)

        if use_splits:
            total = home_split + draw_split + away_split
            if total <= 0:
                st.error("Invalid splits")
            else:
                market_probs = {
                    'home': round((home_split / total) * 100.0, 2),
                    'draw': round((draw_split / total) * 100.0, 2),
                    'away': round((away_split / total) * 100.0, 2)
                }

                true_probs = bot.prediction_model.predict_match_probabilities(
                    home_team, away_team, market_probabilities=market_probs
                )

                edges = {k: round(true_probs[k] - market_probs[k], 2) for k in ['home', 'draw', 'away']}

                st.write("**Team Elo**", f"{home_team}: {home_elo:.1f}", f"{away_team}: {away_elo:.1f}")
                st.write("**Market (from splits)**", market_probs)
                st.write("**Model (true %)**", {k: round(v,2) for k,v in true_probs.items()})
                st.write("**Edges (pp)**", edges)

                # Recommendation: best edge
                best = max(edges.items(), key=lambda x: x[1])
                if best[1] <= 0:
                    st.info("No positive edges found.")
                else:
                    st.markdown("**Recommendation (from splits)**")
                    # For stake sizing we approximate odds from market probs
                    implied_odds = {
                        'home': implied_probability_to_odds(market_probs['home']),
                        'draw': implied_probability_to_odds(market_probs['draw']),
                        'away': implied_probability_to_odds(market_probs['away'])
                    }
                    p = true_probs[best[0]] / 100.0
                    odds = implied_odds[best[0]]
                    stake = calculate_bet_size(bank, p, odds)
                    st.write(f"Bet: {best[0].upper()} | Edge: {best[1]:+.2f}% | Stake: ${stake:.2f} | Odds: {odds:.2f}")

                    # Hedge suggestion: split stake across draw+away proportional to model probs
                    if best[0] == 'away':
                        hedge_total = stake
                        proportion_draw = true_probs['draw'] / (true_probs['draw'] + true_probs['away'])
                        st.write("Hedge idea: split stake between Draw and Away:")
                        st.write(f"  Draw stake: ${hedge_total * proportion_draw:.2f}")
                        st.write(f"  Away stake: ${hedge_total * (1-proportion_draw):.2f}")

        else:
            # Decimal odds path — reuse existing analyzer
            analysis = bot.analyze_match_manual(
                home_team, away_team, home_odds, draw_odds, away_odds,
                home_form=0.0, away_form=0.0, home_goal_diff=0, away_goal_diff=0
            )
            st.write(analysis)

with right:
    st.subheader("Daily Board")
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    st.write(f"Date: {tomorrow}")
    splits_input = st.text_input("Market splits to apply to all fixtures (format: 67/18/15)", value="67/18/15")
    run_board = st.button("Run daily board")
    if run_board:
        # parse splits
        try:
            a,b,c = [int(x.strip()) for x in splits_input.split('/')]
        except Exception:
            st.error("Invalid splits format")
            a=b=c=0

        client = FootballDataClient(api_key=FOOTBALL_DATA_API_KEY)
        matches = client.get_fixtures(date_from=tomorrow, date_to=tomorrow)
        results = []
        for m in matches:
            home = (m.get('homeTeam') or {}).get('name') if isinstance(m.get('homeTeam'), dict) else m.get('homeTeam')
            away = (m.get('awayTeam') or {}).get('name') if isinstance(m.get('awayTeam'), dict) else m.get('awayTeam')
            if not home or not away:
                continue
            market_probs = {'home': round(a/(a+b+c)*100,2), 'draw': round(b/(a+b+c)*100,2), 'away': round(c/(a+b+c)*100,2)}
            true_probs = bot.prediction_model.predict_match_probabilities(home, away, market_probabilities=market_probs)
            edge = true_probs['away'] - market_probs['away']
            results.append({'home': home, 'away': away, 'edge': round(edge,2), 'true': true_probs['away'], 'market': market_probs['away']})

        results_sorted = sorted(results, key=lambda x: -x['edge'])
        st.write("Top matches by Away edge")
        for r in results_sorted[:10]:
            st.write(f"{r['home']} vs {r['away']}: Edge {r['edge']}pp (True {r['true']}% vs Market {r['market']}%)")

    st.subheader("Elo / DB")
    if st.button("Show top 10 Elo ratings"):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT team_name, elo_rating FROM team_ratings ORDER BY elo_rating DESC LIMIT 10")
        rows = cur.fetchall()
        conn.close()
        st.table(rows)

    if st.button("Update Elo from last 7 days results"):
        client = FootballDataClient(api_key=FOOTBALL_DATA_API_KEY)
        today = date.today()
        week_ago = (today - timedelta(days=7)).isoformat()
        matches = client.get_fixtures(date_from=week_ago, date_to=today.isoformat())
        updated = 0
        for m in matches:
            score = m.get('score', {}).get('fullTime', {})
            hs = score.get('home')
            as_ = score.get('away')
            if hs is None or as_ is None:
                continue
            home = (m.get('homeTeam') or {}).get('name') if isinstance(m.get('homeTeam'), dict) else m.get('homeTeam')
            away = (m.get('awayTeam') or {}).get('name') if isinstance(m.get('awayTeam'), dict) else m.get('awayTeam')
            try:
                bot.update_ratings_from_result(home, away, int(hs), int(as_))
                updated += 1
            except Exception:
                continue
        st.success(f"Updated Elo from {updated} recent matches")
