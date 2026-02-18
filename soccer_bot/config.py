"""
Configuration module for soccer betting bot
"""
import os
try:
	from dotenv import load_dotenv
	load_dotenv()
except Exception:
	# `python-dotenv` is optional; if it's not installed, environment variables
	# will be read from the environment only.
	pass

# If an API key wasn't provided via environment or .env, try the example file
if not os.getenv('FOOTBALL_DATA_API_KEY'):
	try:
		# attempt to load .env.example as a fallback
		from dotenv import load_dotenv as _load
		_load('.env.example')
	except Exception:
		pass

# API Configuration
FOOTBALL_DATA_API_KEY = os.getenv('FOOTBALL_DATA_API_KEY', '')
FOOTBALL_DATA_BASE_URL = 'https://api.football-data.org/v4'

# Betting Configuration
BANKROLL = float(os.getenv('BANKROLL', 1000.0))
# Default edge threshold set to 2.5% to match README/Quickstart
EDGE_THRESHOLD = float(os.getenv('EDGE_THRESHOLD', 2.5))  # Minimum edge percentage to bet
USE_FLAT_STAKING = os.getenv('USE_FLAT_STAKING', 'false').lower() == 'true'  # Use flat staking instead of Kelly

# Model Configuration
HOME_ADVANTAGE_ELO = 70  # Home team advantage in Elo points (60-80 recommended)
ELO_K_FACTOR = 32  # Elo rating change factor
INITIAL_ELO = 1500  # Starting Elo rating for new teams

# Staking Configuration
# Default to Half-Kelly to match README examples
KELLY_FRACTION = 0.5  # Use half-Kelly for bet sizing
MAX_STAKE_PERCENT = 5.0  # Maximum stake as % of bankroll per bet
FLAT_STAKE_PERCENT = 1.5  # Flat staking option as % of bankroll

# Calibration Configuration
MARKET_SHRINK_FACTOR = 0.4  # Shrink model probabilities toward market (30-50% recommended)
MIN_PROBABILITY = 5.0  # Minimum probability output (%)
MAX_PROBABILITY = 85.0  # Maximum probability output (%)

# Database Configuration
DB_PATH = 'soccer_bets.db'

# High hit-rate strategy filters
# Minimum model probability (percent) required to consider a favorite
MIN_FAVORITE_PROB = float(os.getenv('MIN_FAVORITE_PROB', 60.0))
# Minimum Elo gap required between teams to consider betting
MIN_ELO_GAP = int(os.getenv('MIN_ELO_GAP', 120))
