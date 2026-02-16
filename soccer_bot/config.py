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
EDGE_THRESHOLD = float(os.getenv('EDGE_THRESHOLD', 2.5))  # Minimum edge percentage to bet

# Model Configuration
HOME_ADVANTAGE = 0.15  # Home team advantage factor
ELO_K_FACTOR = 32  # Elo rating change factor
INITIAL_ELO = 1500  # Starting Elo rating for new teams

# Database Configuration
DB_PATH = 'soccer_bets.db'
