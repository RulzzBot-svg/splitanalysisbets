# Quick Start Guide

## Installation

```bash
# Clone and install
git clone https://github.com/RulzzBot-svg/splitanalysisbets.git
cd splitanalysisbets
pip install -r requirements.txt
```

## 5-Minute Tutorial

### 1. Analyze Your First Match

Let's say you want to bet on a Premier League match. You have these odds:
- Manchester City (Home): 2.10
- Draw: 3.50
- Arsenal (Away): 3.60

```bash
python soccer_bot_cli.py analyze "Manchester City" "Arsenal" 2.10 3.50 3.60
```

The bot will:
- Calculate market probabilities from the odds
- Estimate true probabilities using its model
- Calculate the edge (difference between true and market)
- Recommend a bet if edge ≥ 2.5%
- Calculate optimal stake using Half-Kelly

### 2. Include Form and Stats

You know Man City is in great form (0.5) and Arsenal is struggling (-0.2):

```bash
python soccer_bot_cli.py analyze "Manchester City" "Arsenal" 2.10 3.50 3.60 \
  --home-form 0.5 \
  --away-form -0.2 \
  --home-gd 15 \
  --away-gd 5
```

Form scale: -1 (terrible) to +1 (excellent), 0 = neutral

### 3. Use Interactive Mode

Let the bot ask if you want to place the recommended bet:

```bash
python soccer_bot_cli.py analyze "Liverpool" "Chelsea" 1.90 3.40 4.20 --interactive
```

Type `yes` to place the bet automatically.

### 4. Update Team Ratings

After the match (Man City won 3-1):

```bash
python soccer_bot_cli.py update-ratings "Manchester City" "Arsenal" 3 1
```

This updates both teams' Elo ratings for future predictions.

### 5. Settle Your Bets

Mark your bet as won:

```bash
python soccer_bot_cli.py settle 1 win
```

Options: `win`, `loss`, or `push` (voided)

### 6. Check Your Performance

```bash
python soccer_bot_cli.py stats
```

Shows:
- Win rate
- Total profit/loss
- ROI
- Current bankroll

## Common Workflows

### Workflow A: Quick Analysis

```bash
# Analyze a match
python soccer_bot_cli.py analyze "Barcelona" "Real Madrid" 2.30 3.20 3.10

# If edge is good, place the bet via interactive mode
python soccer_bot_cli.py analyze "Barcelona" "Real Madrid" 2.30 3.20 3.10 --interactive
```

### Workflow B: Multiple Matches

```bash
# Analyze several matches
python soccer_bot_cli.py analyze "Bayern" "Dortmund" 1.80 3.60 4.50
python soccer_bot_cli.py analyze "PSG" "Lyon" 1.65 3.80 5.50
python soccer_bot_cli.py analyze "Juventus" "Inter" 2.40 3.10 3.00

# Check which bets you placed
python soccer_bot_cli.py list-bets --pending
```

### Workflow C: Weekly Routine

**Before matches:**
```bash
# Analyze upcoming matches with all available info
python soccer_bot_cli.py analyze "Team A" "Team B" 2.00 3.20 3.50 \
  --home-form 0.3 --away-form -0.1 --home-gd 8 --away-gd -2 \
  --interactive
```

**After matches:**
```bash
# Update ratings
python soccer_bot_cli.py update-ratings "Team A" "Team B" 2 1

# Settle bets
python soccer_bot_cli.py settle 1 win
python soccer_bot_cli.py settle 2 loss

# Check stats
python soccer_bot_cli.py stats
```

## Understanding the Output

### Edge Calculation

```
Edge = True Probability - Market Probability
```

- **Positive edge**: Your model thinks the outcome is more likely than the market
- **Edge ≥ 2.5%**: Recommended bet threshold
- **Higher edge**: More confident bet, larger stake

### Bet Sizing (Half-Kelly)

The bot uses Half-Kelly for safety:
- Conservative growth
- Lower variance
- Typically recommends 1-10% of bankroll per bet
- Never more than 25% on a single bet

### Example Output Explained

```
Market Probabilities: Home 45.8%, Draw 27.5%, Away 26.7%
True Probabilities:   Home 40.1%, Draw 23.9%, Away 36.0%
Edges:                Home -5.7%, Draw -3.6%, Away +9.2%
```

Interpretation:
- Home: Market overvalues home team (negative edge)
- Away: Market undervalues away team (9.2% edge!)
- **Recommendation**: Bet on Away

## Tips for Success

### 1. Start Small
Begin with a modest bankroll ($100-$500) while you learn the system.

### 2. Track Results
```bash
python soccer_bot_cli.py stats
```
Run this weekly to monitor performance.

### 3. Update Ratings Regularly
After every match you analyze, update ratings:
```bash
python soccer_bot_cli.py update-ratings "Home" "Away" 2 1
```

### 4. Use Form Data
Recent form matters! Include it when you can:
- Last 5 matches: 5W = +0.5, 5L = -0.5
- Last 5 matches: 3W 2D = +0.2

### 5. Don't Force Bets
No edge? No bet! The threshold is there for a reason.

### 6. Review Pending Bets
```bash
python soccer_bot_cli.py list-bets --pending
```

## Configuration

Edit `.env` file (create from `.env.example`):

```env
BANKROLL=1000.0        # Your starting bankroll
EDGE_THRESHOLD=2.5     # Minimum edge to bet (%)
```

Higher threshold = fewer but stronger bets

## Troubleshooting

**No bets recommended?**
- Threshold might be too high
- Market odds might be efficient
- Try matches where you have form/GD data

**Stakes seem too high?**
- Check your BANKROLL setting
- Remember: Half-Kelly is aggressive for some
- You can manually scale down stakes

**Database errors?**
- Delete `soccer_bets.db` to reset
- All data will be lost

## Next Steps

1. **Run the examples**: `python examples.py`
2. **Analyze real matches**: Find odds from bookmakers
3. **Track 10-20 bets**: Build confidence in the system
4. **Fine-tune**: Adjust threshold, bankroll settings

## Advanced: API Integration (Future)

To automate with football-data.org:

1. Get API key from https://www.football-data.org/
2. Add to `.env`: `FOOTBALL_DATA_API_KEY=your_key`
3. Use the API client in `soccer_bot/api_client.py`

(Full automation coming soon!)

## Resources

- **README.md**: Full documentation
- **examples.py**: Code examples
- **soccer_bot/**: Core library modules

## Questions?

See the full README.md or open an issue on GitHub!
