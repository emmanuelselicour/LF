# Configuration GPT-Bet.Foot
CONFIG = {
    "api_key": "your_openai_api_key",
    "min_edge": 3.0,  # Edge minimum en %
    "kelly_factor": 0.25,
    "max_stake_percent": 5.0,
    "bankroll": 10000,
    "required_confidence": 0.6,
    "leagues": ["Ligue 1", "Premier League", "La Liga", "Bundesliga", "Serie A"],
    "bet_types": ["1X2", "Over/Under", "Both Teams to Score"]
}

# Modèle probabiliste
MODEL_WEIGHTS = {
    "xg_weight": 0.3,
    "ranking_weight": 0.2, 
    "form_weight": 0.1,
    "home_advantage": 0.15,
    "margin": 0.055  # Marge bookmaker
}
