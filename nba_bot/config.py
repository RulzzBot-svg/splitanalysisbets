"""
Configuration module for NBA betting bot
"""
import os


def _load_env_fallback(path: str = '.env') -> None:
    """Load .env without python-dotenv (minimal KEY=VALUE parser)."""
    if not os.path.isfile(path):
        return
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key:
                    os.environ.setdefault(key, value)
    except Exception:
        return


try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    _load_env_fallback()

# API Configuration
NBA_API_KEY = os.getenv('NBA_API_KEY')
NBA_ELO_CSV = os.getenv('NBA_ELO_CSV')

# Betting Configuration
BANKROLL = float(os.getenv('NBA_BANKROLL', os.getenv('BANKROLL', 1000.0)))
EDGE_THRESHOLD = float(os.getenv('NBA_EDGE_THRESHOLD', 1.0))  # Minimum edge % to bet (NBA: 1%)

# Model Configuration
# Home court advantage expressed in Elo points (~equivalent to +50 Elo)
HOME_COURT_ELO = int(os.getenv('NBA_HOME_COURT_ELO', 50))
# Extra Elo per additional rest day (e.g. team with 2 days rest vs 1 day = +15 Elo)
REST_ELO_PER_DAY = int(os.getenv('NBA_REST_ELO_PER_DAY', 15))
# Elo penalty for a team playing on a back-to-back (second game in consecutive nights)
B2B_PENALTY_ELO = int(os.getenv('NBA_B2B_PENALTY_ELO', 30))
# Elo penalty when a star player is manually flagged as out
STAR_OUT_PENALTY_ELO = int(os.getenv('NBA_STAR_OUT_PENALTY_ELO', 50))

# Elo System
ELO_K_FACTOR = int(os.getenv('NBA_ELO_K_FACTOR', 20))
INITIAL_ELO = int(os.getenv('NBA_INITIAL_ELO', 1500))

# Staking Configuration
KELLY_FRACTION = 0.5       # Half-Kelly
MAX_STAKE_PERCENT = 5.0    # Maximum stake as % of bankroll
FLAT_STAKE_PERCENT = 1.5   # Flat staking: 1.5% of bankroll
USE_FLAT_STAKING = os.getenv('NBA_USE_FLAT_STAKING', 'true').lower() == 'true'

# Probability calibration
MARKET_SHRINK_FACTOR = 0.3  # Shrink model prob toward market
MIN_PROBABILITY = 5.0
MAX_PROBABILITY = 95.0

# High hit-rate strategy filters (NBA)
# Only bet the favorite; require model_prob >= 62% and model_prob >= market_prob + 1%
MIN_FAVORITE_PROB = float(os.getenv('NBA_MIN_FAVORITE_PROB', 62.0))
MIN_EDGE = float(os.getenv('NBA_MIN_EDGE', 1.0))  # model_prob must exceed market_prob by at least this %

# Database
DB_PATH = os.getenv('NBA_DB_PATH', 'nba_bets.db')
