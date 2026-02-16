"""
Configuration module for soccer betting bot
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
FOOTBALL_DATA_API_KEY = os.getenv('FOOTBALL_DATA_API_KEY', '')
FOOTBALL_DATA_BASE_URL = 'https://api.football-data.org/v4'

# Betting Configuration
BANKROLL = float(os.getenv('BANKROLL', 1000.0))
EDGE_THRESHOLD = float(os.getenv('EDGE_THRESHOLD', 5.0))  # Minimum edge percentage to bet (increased from 2.5% to 5%)
USE_FLAT_STAKING = os.getenv('USE_FLAT_STAKING', 'false').lower() == 'true'  # Use flat staking instead of Kelly

# Model Configuration
HOME_ADVANTAGE_ELO = 70  # Home team advantage in Elo points (60-80 recommended)
ELO_K_FACTOR = 32  # Elo rating change factor
INITIAL_ELO = 1500  # Starting Elo rating for new teams

# Staking Configuration
KELLY_FRACTION = 0.25  # Use quarter-Kelly for conservative staking (was 0.5)
MAX_STAKE_PERCENT = 5.0  # Maximum stake as % of bankroll per bet
FLAT_STAKE_PERCENT = 1.5  # Flat staking option as % of bankroll

# Calibration Configuration
MARKET_SHRINK_FACTOR = 0.4  # Shrink model probabilities toward market (30-50% recommended)
MIN_PROBABILITY = 5.0  # Minimum probability output (%)
MAX_PROBABILITY = 85.0  # Maximum probability output (%)

# Database Configuration
DB_PATH = 'soccer_bets.db'
