"""
API client for fetching fixtures from football-data.org
"""
import requests
from typing import List, Dict, Optional
from soccer_bot.config import FOOTBALL_DATA_API_KEY, FOOTBALL_DATA_BASE_URL


class FootballDataClient:
    """Client for football-data.org API"""
    
    def __init__(self, api_key: str = FOOTBALL_DATA_API_KEY):
        self.api_key = api_key
        self.base_url = FOOTBALL_DATA_BASE_URL
        self.headers = {
            'X-Auth-Token': self.api_key
        }
    
    def get_fixtures(self, competition_id: Optional[str] = None, 
                     date_from: Optional[str] = None,
                     date_to: Optional[str] = None) -> List[Dict]:
        """
        Fetch fixtures from football-data.org
        
        Args:
            competition_id: Optional competition ID (e.g., 'PL' for Premier League)
            date_from: Optional start date (YYYY-MM-DD)
            date_to: Optional end date (YYYY-MM-DD)
            
        Returns:
            List of fixture dictionaries
        """
        if competition_id:
            url = f"{self.base_url}/competitions/{competition_id}/matches"
        else:
            url = f"{self.base_url}/matches"
        
        params = {}
        if date_from:
            params['dateFrom'] = date_from
        if date_to:
            params['dateTo'] = date_to
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('matches', [])
        except requests.RequestException as e:
            print(f"Error fetching fixtures: {e}")
            return []
    
    def get_team_info(self, team_id: int) -> Optional[Dict]:
        """
        Fetch team information
        
        Args:
            team_id: Team ID
            
        Returns:
            Team information dictionary
        """
        url = f"{self.base_url}/teams/{team_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching team info: {e}")
            return None
