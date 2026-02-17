"""
Database management for tracking bets and results
"""
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime
from soccer_bot.config import DB_PATH
from soccer_bot.model import normalize_team_name


class BettingDatabase:
    """Manage SQLite database for bet tracking"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create bets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                bet_type TEXT NOT NULL,
                odds REAL NOT NULL,
                stake REAL NOT NULL,
                true_probability REAL NOT NULL,
                market_probability REAL NOT NULL,
                edge REAL NOT NULL,
                result TEXT,
                profit_loss REAL,
                match_date TEXT
            )
        """)
        
        # Create team ratings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_ratings (
                team_name TEXT PRIMARY KEY,
                elo_rating REAL NOT NULL,
                last_updated TEXT NOT NULL
            )
        """)
        
        # Create match results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS match_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_date TEXT NOT NULL,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_score INTEGER NOT NULL,
                away_score INTEGER NOT NULL,
                competition TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_bet(self, home_team: str, away_team: str, bet_type: str,
                odds: float, stake: float, true_probability: float,
                market_probability: float, edge: float,
                match_date: Optional[str] = None) -> int:
        """
        Add a new bet to the database
        
        Args:
            home_team: Home team name
            away_team: Away team name
            bet_type: Type of bet ('home', 'draw', 'away')
            odds: Decimal odds
            stake: Bet amount
            true_probability: Estimated true probability (%)
            market_probability: Market implied probability (%)
            edge: Calculated edge (%)
            match_date: Optional match date
            
        Returns:
            Bet ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO bets (
                timestamp, home_team, away_team, bet_type, odds, stake,
                true_probability, market_probability, edge, match_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, home_team, away_team, bet_type, odds, stake,
              true_probability, market_probability, edge, match_date))
        
        bet_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return bet_id
    
    def update_bet_result(self, bet_id: int, result: str, profit_loss: float):
        """
        Update bet with result
        
        Args:
            bet_id: Bet ID
            result: Result ('win', 'loss', 'push')
            profit_loss: Profit or loss amount
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE bets
            SET result = ?, profit_loss = ?
            WHERE id = ?
        """, (result, profit_loss, bet_id))
        
        conn.commit()
        conn.close()
    
    def get_all_bets(self) -> List[Dict]:
        """Get all bets from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM bets")
        rows = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        bets = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        return bets
    
    def get_pending_bets(self) -> List[Dict]:
        """Get bets without results"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM bets WHERE result IS NULL")
        rows = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        bets = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        return bets
    
    def save_team_rating(self, team_name: str, elo_rating: float):
        """Save team Elo rating"""
        conn = self.get_connection()
        cursor = conn.cursor()

        timestamp = datetime.now().isoformat()
        team_key = normalize_team_name(team_name)

        cursor.execute("""
            INSERT OR REPLACE INTO team_ratings (team_name, elo_rating, last_updated)
            VALUES (?, ?, ?)
        """, (team_key, elo_rating, timestamp))

        conn.commit()
        conn.close()
    
    def load_team_ratings(self) -> Dict[str, float]:
        """Load all team ratings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT team_name, elo_rating FROM team_ratings")
        rows = cursor.fetchall()

        ratings: Dict[str, float] = {}
        for row in rows:
            key = normalize_team_name(row[0])
            # last row wins; if duplicates exist we overwrite with normalized key
            ratings[key] = row[1]

        conn.close()
        return ratings
    
    def add_match_result(self, match_date: str, home_team: str, away_team: str,
                        home_score: int, away_score: int, competition: str = None):
        """Add match result to database"""
        conn = self.get_connection()
        cursor = conn.cursor()

        home_key = normalize_team_name(home_team)
        away_key = normalize_team_name(away_team)

        cursor.execute("""
            INSERT INTO match_results (
                match_date, home_team, away_team, home_score, away_score, competition
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (match_date, home_key, away_key, home_score, away_score, competition))

        conn.commit()
        conn.close()
    
    def get_betting_stats(self) -> Dict:
        """Calculate betting statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total bets
        cursor.execute("SELECT COUNT(*) FROM bets")
        total_bets = cursor.fetchone()[0]
        
        # Settled bets
        cursor.execute("SELECT COUNT(*) FROM bets WHERE result IS NOT NULL")
        settled_bets = cursor.fetchone()[0]
        
        # Wins
        cursor.execute("SELECT COUNT(*) FROM bets WHERE result = 'win'")
        wins = cursor.fetchone()[0]
        
        # Total staked
        cursor.execute("SELECT SUM(stake) FROM bets")
        total_staked = cursor.fetchone()[0] or 0.0
        
        # Total profit/loss
        cursor.execute("SELECT SUM(profit_loss) FROM bets WHERE profit_loss IS NOT NULL")
        total_pl = cursor.fetchone()[0] or 0.0
        
        conn.close()
        
        win_rate = (wins / settled_bets * 100) if settled_bets > 0 else 0.0
        roi = (total_pl / total_staked * 100) if total_staked > 0 else 0.0
        
        return {
            'total_bets': total_bets,
            'settled_bets': settled_bets,
            'pending_bets': total_bets - settled_bets,
            'wins': wins,
            'losses': settled_bets - wins,
            'win_rate': win_rate,
            'total_staked': total_staked,
            'total_profit_loss': total_pl,
            'roi': roi
        }
