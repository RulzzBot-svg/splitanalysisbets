# Soccer Betting Decision Bot

A sophisticated soccer betting analysis tool that helps identify value bets by comparing true win probabilities (calculated using Elo ratings, form, goal difference, and home advantage) against market odds. The bot uses Half-Kelly criterion for optimal bet sizing and tracks all bets in SQLite.

## Features

- 🎯 **Edge Detection**: Calculates the difference between true probability and market probability
- 📊 **Elo Rating System**: Maintains team ratings that update based on match results
- 🏠 **Home Advantage**: Accounts for home field advantage in predictions
- 📈 **Form Analysis**: Incorporates recent team form and goal difference
- 💰 **Kelly Criterion**: Uses Half-Kelly for optimal bet sizing based on bankroll
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
- Calculate true probabilities using the model
- Show the edge for each outcome
- Recommend a bet if edge ≥ threshold (default 2.5%)
- Calculate optimal stake using Half-Kelly

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

### 2. True Probability Estimation

Uses multiple factors to estimate the true win probability:

- **Elo Ratings**: Base team strength (starts at 1500)
- **Home Advantage**: ~15% boost for home team
- **Recent Form**: ±10 Elo points per 0.1 form
- **Goal Difference**: ±5 Elo points per goal (capped at ±5 goals)

### 3. Edge Calculation

```
Edge = True Probability - Market Probability
```

Only bet when edge ≥ threshold (default 2.5%)

### 4. Bet Sizing (Half-Kelly)

```
Kelly Fraction = (odds * probability - 1) / (odds - 1)
Half Kelly = Kelly Fraction * 0.5
Stake = Bankroll * Half Kelly
```

Caps at 25% of bankroll for safety.

## Configuration

Edit `.env` file:

```env
# API Configuration (for future automation)
FOOTBALL_DATA_API_KEY=your_api_key_here

# Betting Configuration
BANKROLL=1000.0
EDGE_THRESHOLD=2.5
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

If your true probability estimate is 60% but the market implies 50%, you have a 10% edge. Over many bets, this edge translates to profit.

### Why Half-Kelly

Full Kelly maximizes long-term growth but has high variance. Half-Kelly provides:
- Lower risk of ruin
- Smoother bankroll growth
- Still optimal long-term returns
- More practical for real betting

### Elo Rating System

Teams start at 1500 and gain/lose points based on match results. Expected score formula:

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

## License

MIT License - Feel free to use and modify!

## Disclaimer

⚠️ **This tool is for educational purposes only.** Gambling involves risk. Never bet more than you can afford to lose. Past performance does not guarantee future results. Always gamble responsibly.
