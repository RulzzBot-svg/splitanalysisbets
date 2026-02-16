# Soccer Betting Decision Bot

A professional-grade soccer betting analysis tool that helps identify value bets by comparing true win probabilities (calculated using Elo ratings, form, goal difference, and home advantage) against market odds. The bot uses Quarter-Kelly criterion for optimal bet sizing, includes market calibration, and tracks all bets in SQLite.

## 🎯 Recent Improvements (v2.0)

This version includes major improvements to make the model professionally testable:

1. **✅ Enhanced Elo System**: Home advantage now properly calibrated at 70 Elo points (vs 15% factor), verified logistic conversion formula
2. **✅ Conservative Staking**: Default changed from Half-Kelly (0.5) to Quarter-Kelly (0.25) with 5% max stake cap
3. **✅ Market Calibration**: Probabilities shrunk 40% toward market to prevent overconfident predictions
4. **✅ Higher Edge Threshold**: Minimum edge increased from 2.5% to 5% for more selective betting
5. **📊 Backtest Ready**: Structure prepared for historical data validation (databases recommended below)

## Features

- 🎯 **Edge Detection**: Calculates the difference between true probability and market probability
- 📊 **Improved Elo Rating System**: Maintains team ratings with properly calibrated home advantage (70 Elo points)
- 🏠 **Home Advantage**: Scientific home field advantage adjustment based on Elo research
- 📈 **Form Analysis**: Incorporates recent team form and goal difference
- 💰 **Quarter-Kelly Staking**: Conservative bet sizing with configurable Kelly fraction (0.25 default)
- 🎚️ **Market Calibration**: Shrinks model predictions toward market to prevent overconfidence
- 💾 **SQLite Tracking**: Stores all bets, results, and team ratings
- 🔍 **Manual Mode**: Start simple with manual odds input
- 🤖 **Automated Ready**: Structure ready for API integration with football-data.org

## Installation

1. Clone the repository:
```bash
git clone https://github.com/RulzzBot-svg/splitanalysisbets.git
cd splitanalysisbets
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Set up configuration:
```bash
cp .env.example .env
# Edit .env with your settings
```

## Quick Start

### Analyze a Match

Analyze a match with market odds and get betting recommendations:

```bash
python soccer_bot_cli.py analyze "Manchester City" "Arsenal" 2.10 3.50 3.60
```

This will:
- Convert odds to market probabilities
- Calculate true probabilities using the model (with market calibration)
- Show the edge for each outcome
- Recommend a bet if edge ≥ threshold (default 5%)
- Calculate optimal stake using Quarter-Kelly (0.25 fraction)

### Analyze with Additional Factors

Include form and goal difference:

```bash
python soccer_bot_cli.py analyze "Liverpool" "Chelsea" 1.90 3.40 4.20 \
  --home-form 0.5 \
  --away-form -0.2 \
  --home-gd 15 \
  --away-gd 5
```

Parameters:
- `--home-form`: Recent form (-1 to 1, where 0.5 = good form, -0.5 = poor form)
- `--away-form`: Recent form for away team
- `--home-gd`: Goal difference for home team
- `--away-gd`: Goal difference for away team

### Interactive Betting

Use interactive mode to place bets directly:

```bash
python soccer_bot_cli.py analyze "Real Madrid" "Barcelona" 2.50 3.30 2.80 --interactive
```

The bot will ask if you want to place the recommended bet.

### Update Team Ratings

After matches finish, update team Elo ratings:

```bash
python soccer_bot_cli.py update-ratings "Manchester City" "Arsenal" 3 1
```

This updates both teams' ratings based on the result and stores them in the database.

### Settle Bets

Mark bets as won, lost, or pushed:

```bash
python soccer_bot_cli.py settle 1 win
```

### View Statistics

See your betting performance:

```bash
python soccer_bot_cli.py stats
```

Displays:
- Current bankroll
- Total bets placed
- Win rate
- Total P/L
- ROI

### List Bets

View all bets or just pending ones:

```bash
# All bets
python soccer_bot_cli.py list-bets

# Pending bets only
python soccer_bot_cli.py list-bets --pending
```

## How It Works

### 1. Market Probability Calculation

Converts bookmaker odds to implied probabilities and removes the bookmaker's margin:

```python
# Example: Odds of 2.50 → 40% implied probability
market_prob = (1 / 2.50) * 100 = 40%
```

### 2. True Probability Estimation (Improved Elo Model)

Uses multiple factors to estimate the true win probability:

- **Elo Ratings**: Base team strength (starts at 1500)
- **Home Advantage**: +70 Elo points for home team (based on research showing ~60-80 point advantage)
- **Recent Form**: ±10 Elo points per 0.1 form factor
- **Goal Difference**: ±5 Elo points per goal (capped at ±5 goals)
- **Logistic Formula**: `P(win) = 1 / (1 + 10^((Elo_opponent - Elo_team) / 400))`

### 3. Market Calibration

To prevent overconfident predictions, model probabilities are shrunk toward market:

```
Calibrated_Prob = (1 - α) * Model_Prob + α * Market_Prob
```

Where α = 0.4 (40% shrinkage toward market). This prevents extreme divergence from market consensus.

### 4. Edge Calculation

```
Edge = True Probability - Market Probability
```

Only bet when edge ≥ threshold (default 5%, increased from 2.5% for more selective betting)

### 5. Bet Sizing (Quarter-Kelly)

```
Kelly Fraction = (odds * probability - 1) / (odds - 1)
Quarter Kelly = Kelly Fraction * 0.25
Stake = Bankroll * Quarter Kelly
```

Capped at 5% of bankroll for safety. Alternatively, use flat staking (1.5% of bankroll) via `USE_FLAT_STAKING=true`.

## Configuration

Edit `.env` file:

```env
# API Configuration (for future automation)
FOOTBALL_DATA_API_KEY=your_api_key_here

# Betting Configuration
BANKROLL=1000.0              # Your bankroll
EDGE_THRESHOLD=5.0           # Minimum edge to bet (% - increased from 2.5%)
USE_FLAT_STAKING=false       # Use flat 1.5% staking instead of Kelly
```

### Advanced Configuration (in `config.py`)

```python
# Elo Configuration
HOME_ADVANTAGE_ELO = 70      # Home advantage in Elo points (60-80 recommended)
ELO_K_FACTOR = 32           # Rating change speed

# Staking Configuration  
KELLY_FRACTION = 0.25       # Quarter-Kelly (0.25), more conservative than Half-Kelly
MAX_STAKE_PERCENT = 5.0     # Never stake more than 5% on single bet
FLAT_STAKE_PERCENT = 1.5    # Flat staking amount when enabled

# Calibration Configuration
MARKET_SHRINK_FACTOR = 0.4  # Shrink 40% toward market (0.3-0.5 recommended)
MIN_PROBABILITY = 5.0       # Minimum probability output
MAX_PROBABILITY = 85.0      # Maximum probability output
```

## Project Structure

```
splitanalysisbets/
├── soccer_bot/
│   ├── __init__.py
│   ├── api_client.py      # Football-data.org API client
│   ├── betting.py         # Kelly criterion and bet sizing
│   ├── bot.py            # Main bot orchestrator
│   ├── config.py         # Configuration management
│   ├── database.py       # SQLite database operations
│   ├── model.py          # Elo ratings and prediction model
│   └── probability.py    # Odds conversion utilities
├── soccer_bot_cli.py     # Command-line interface
├── requirements.txt
└── README.md
```

## Examples

### Example 1: Finding Value

```bash
$ python soccer_bot_cli.py analyze "Bayern Munich" "Dortmund" 1.80 3.80 4.50

======================================================================
MATCH ANALYSIS: Bayern Munich vs Dortmund
======================================================================

Team Elo Ratings:
  Bayern Munich: 1500
  Dortmund: 1500

Market Probabilities (implied from odds):
  Home: 53.55%
  Draw: 25.37%
  Away: 21.43%

Model (True) Probabilities:
  Home: 56.15%
  Draw: 22.50%
  Away: 21.35%

Edges (True - Market):
  Home: +2.60%
  Draw: -2.87%
  Away: -0.08%

**********************************************************************
BETTING RECOMMENDATION:
**********************************************************************
  Bet Type: HOME
  Odds: 1.8
  Recommended Stake: $32.50
  Edge: +2.60%
  True Probability: 56.15%
  Market Probability: 53.55%
  Potential Return: $58.50
  Potential Profit: $26.00
**********************************************************************
```

### Example 2: No Value Found

```bash
$ python soccer_bot_cli.py analyze "Team A" "Team B" 2.00 3.00 4.00

No bet recommended (edge below 2.5% threshold)
```

### Example 3: Tracking Performance

```bash
$ python soccer_bot_cli.py stats

======================================================================
BETTING STATISTICS
======================================================================
Current Bankroll: $1,050.25

Total Bets: 15
  Settled: 12
  Pending: 3

Results:
  Wins: 7
  Losses: 5
  Win Rate: 58.3%

Financials:
  Total Staked: $450.00
  Total P/L: $50.25
  ROI: 11.17%
```

## 📊 Historical Data Sources for Backtesting

To validate and improve the model, you need historical match data with:
- Match results (scores, dates)
- Market odds (preferably closing odds)
- Team statistics (optional: xG, possession, shots, etc.)

### Recommended Data Sources

#### 1. **Football-Data.co.uk** (FREE - Recommended)
- **URL**: https://www.football-data.co.uk/
- **Coverage**: Major European leagues (EPL, La Liga, Serie A, Bundesliga, Ligue 1)
- **Data**: Match results, closing odds from multiple bookmakers, basic stats
- **Format**: CSV files (easy to parse)
- **History**: 20+ years for major leagues
- **Best For**: Backtesting odds-based models

#### 2. **API-Football (RapidAPI)** (FREEMIUM)
- **URL**: https://www.api-football.com/
- **Coverage**: 1000+ leagues worldwide
- **Data**: Real-time and historical fixtures, odds, statistics, lineups, injuries
- **Format**: JSON API
- **Free Tier**: 100 requests/day
- **Best For**: Real-time integration and comprehensive stats

#### 3. **Understat** (FREE - Web Scraping)
- **URL**: https://understat.com/
- **Coverage**: Top 5 European leagues
- **Data**: xG (expected goals), xGA, detailed shot data
- **Format**: Requires web scraping
- **Best For**: Advanced xG-based models

#### 4. **FiveThirtyEight SPI** (FREE)
- **URL**: https://projects.fivethirtyeight.com/soccer-predictions/
- **Coverage**: Major leagues
- **Data**: Team ratings (SPI), match predictions, probabilities
- **Format**: CSV downloads
- **Best For**: Comparing your Elo model against professional ratings

#### 5. **ClubElo.com** (FREE)
- **URL**: http://clubelo.com/
- **Coverage**: 100+ leagues
- **Data**: Updated Elo ratings for teams
- **Format**: CSV downloads
- **Best For**: Seeding your model with real Elo ratings instead of default 1500

#### 6. **Sofascore API** (FREE with limits)
- **URL**: https://www.sofascore.com/
- **Coverage**: Global coverage
- **Data**: Match data, lineups, statistics
- **Format**: API (unofficial)
- **Best For**: Recent match data and statistics

### How to Use Historical Data

1. **Download historical data** (e.g., from Football-Data.co.uk)
2. **Create a backtesting script** that:
   - Loads historical matches
   - For each match, predicts outcome using your model
   - Compares prediction to actual result
   - Tracks ROI if you had bet based on your edges
3. **Validate calibration**: If model says 40% win probability, do teams win ~40% of the time?
4. **Compare vs closing market odds** to see if your edge is real

### Example: Getting Started with Football-Data.co.uk

```python
import pandas as pd

# Download CSV from https://www.football-data.co.uk/englandm.php
# Example: Premier League 2023-24
df = pd.read_csv('E0.csv')  # E0 = Premier League

# Columns include:
# - Date, HomeTeam, AwayTeam
# - FTHG (Full Time Home Goals), FTAG (Full Time Away Goals)
# - B365H, B365D, B365A (Bet365 odds for Home/Draw/Away)
# - PSH, PSD, PSA (Pinnacle Sports odds - often used as "sharp" closing odds)

for _, match in df.iterrows():
    # Use closing odds (e.g., Pinnacle)
    home_odds = match['PSH']
    draw_odds = match['PSD']
    away_odds = match['PSA']
    
    # Your model prediction
    analysis = bot.analyze_match_manual(
        match['HomeTeam'], match['AwayTeam'],
        home_odds, draw_odds, away_odds
    )
    
    # Compare to actual result
    actual_result = 'home' if match['FTHG'] > match['FTAG'] else \
                   'away' if match['FTAG'] > match['FTHG'] else 'draw'
    
    # Track if your edge translated to profit
    # ... (implement backtesting logic)
```

## Future Enhancements

- [ ] Automated fixture fetching from football-data.org
- [ ] Backtesting module for strategy validation
- [ ] Web interface
- [ ] Additional models (Poisson, machine learning)
- [ ] Multi-league support
- [ ] Live odds monitoring
- [ ] Automated bet placement integration

## Theory

### Why Edge Matters

If your true probability estimate is 60% but the market implies 50%, you have a 10% edge. Over many bets, this edge translates to profit. However, edges should be:
- **Significant**: At least 5-7% to overcome transaction costs and variance
- **Real**: Validated against closing market odds (not just any bookmaker)
- **Consistent**: Test on 200-500 historical matches before betting real money

### Why Quarter-Kelly (Not Full Kelly)

Full Kelly maximizes long-term growth but has extreme variance. Quarter-Kelly provides:
- **Much lower risk of ruin** compared to Full Kelly
- **Smoother bankroll growth** with less volatility
- **Still good long-term returns** (75% of Full Kelly growth rate)
- **More practical for real betting** with imperfect probability estimates
- **Built-in safety margin** for model uncertainty

| Strategy | Growth Rate | Volatility | Risk of Ruin |
|----------|-------------|------------|--------------|
| Full Kelly | 100% | Very High | Moderate |
| Half Kelly | 87.5% | High | Low |
| **Quarter Kelly** | **75%** | **Moderate** | **Very Low** |
| Flat 2% | ~40% | Low | Very Low |

### Market Calibration

No model is perfect. Market calibration prevents overconfidence:

```
Calibrated = 0.6 × Model + 0.4 × Market
```

This means:
- If model says 70% and market says 50%, calibrated = 62%
- Prevents extreme divergence from market wisdom
- Market represents aggregate of thousands of sharp bettors
- Use market as a "sanity check" on your model

### Elo Rating System

Teams start at 1500 and gain/lose points based on match results. Expected score formula (logistic):

```
E_A = 1 / (1 + 10^((R_B - R_A) / 400))
```

After a match:
```
R_A_new = R_A + K * (S_A - E_A)
```

Where:
- `K` = 32 (rating change factor)
- `S_A` = actual score (1 for win, 0.5 for draw, 0 for loss)
- `E_A` = expected score

**Home Advantage**: Research shows home teams have a 60-80 Elo point advantage. This model uses 70 Elo points, which translates to roughly:
- Equal teams (both 1500): Home wins ~60%, Draw ~25%, Away ~15%
- This matches real-world home win percentages in major leagues

## 🚀 Professional Usage Recommendations

### Before Betting Real Money

1. **Backtest on 200-500 historical matches**
   - Download data from Football-Data.co.uk
   - Track predicted vs actual outcomes
   - Calculate ROI as if you had bet
   - Check calibration: Does 40% probability = 40% actual wins?

2. **Seed with real Elo ratings**
   - Download current ratings from ClubElo.com
   - Load into database instead of using default 1500
   - This immediately improves accuracy

3. **Use closing odds, not opening**
   - Closing odds are more efficient (incorporate all information)
   - Compare your edges to closing lines
   - If frequently disagreeing by 20%+, recalibrate

4. **Paper trade first**
   - Track bets for 30-50 matches without real money
   - Validate your edge is real before risking capital

### When to Bet

Only bet when ALL conditions are met:
- ✅ Edge ≥ 5% (preferably 7%+)
- ✅ You have confidence in your inputs (form, GD, etc.)
- ✅ Market odds are closing odds (not early/opening)
- ✅ Bet size is comfortable (should not stress you)
- ✅ Model agrees with your own analysis

### Red Flags (Don't Bet)

- ❌ Edge is there but you don't understand why
- ❌ Model severely disagrees with sharp market (e.g., Pinnacle)
- ❌ Incomplete data (missing form, GD, recent matches)
- ❌ Your model shows 40% but market shows 15% (too extreme)
- ❌ Emotional attachment to a team

### Improving the Model

**Next Steps for Advanced Users:**

1. **Add xG data**: Expected goals are highly predictive
2. **Track injuries/suspensions**: Key player availability matters
3. **Recent form**: Implement proper form calculation (W=3, D=1, L=0 over last 5)
4. **Head-to-head history**: Some teams match up better than others
5. **Team value/quality**: Use Transfermarkt values as team strength proxy
6. **Rest days**: Teams with more rest perform better
7. **Motivation factors**: Teams fighting relegation vs mid-table with nothing to play for

## License

MIT License - Feel free to use and modify!

## Disclaimer

⚠️ **This tool is for educational purposes only.** Gambling involves risk. Never bet more than you can afford to lose. Past performance does not guarantee future results. Always gamble responsibly.

**Important Notes:**
- This model has been improved with professional best practices, but it is NOT guaranteed to be profitable
- ALWAYS backtest thoroughly before risking real money
- Markets are efficient - consistently beating them is extremely difficult
- Use proper bankroll management and never bet money you can't afford to lose
- Consider this a learning tool and starting point, not a "get rich quick" system
