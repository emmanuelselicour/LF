"""
GPT-Bet.Foot Core Functions
Core betting functions using only OpenAI ecosystem
"""

import json
import math
from typing import Dict, Tuple

def fair_odds(delta_xg: float, delta_ranking: float, delta_days: float) -> Dict[str, float]:
    """
    Calculate fair odds using simplified Bayesian model
    
    Args:
        delta_xg: Expected goals difference (home - away)
        delta_ranking: Team ranking difference (home - away)
        delta_days: Days since last match difference (home - away)
    
    Returns:
        Dictionary with probabilities and fair odds
    """
    # Calculate raw probability using logistic function
    linear_combination = 0.3 * delta_xg + 0.2 * delta_ranking + 0.1 * delta_days
    
    # Home win probability
    p_home = 1 / (1 + math.exp(-linear_combination))
    
    # Away win probability (symmetrical)
    p_away = 1 / (1 + math.exp(linear_combination))
    
    # Draw probability (remaining)
    p_draw = 1 - p_home - p_away
    
    # Ensure probabilities are valid
    if p_draw < 0:
        # Normalize if sum exceeds 1
        total = p_home + p_away
        p_home = p_home / total
        p_away = p_away / total
        p_draw = 0
    
    # Calculate fair odds (inverse of probability)
    fair_home = 1 / p_home if p_home > 0 else float('inf')
    fair_draw = 1 / p_draw if p_draw > 0 else float('inf')
    fair_away = 1 / p_away if p_away > 0 else float('inf')
    
    return {
        'probabilities': {
            'home': round(p_home, 4),
            'draw': round(p_draw, 4),
            'away': round(p_away, 4)
        },
        'fair_odds': {
            'home': round(fair_home, 2),
            'draw': round(fair_draw, 2),
            'away': round(fair_away, 2)
        }
    }

def kelly(edge: float, fair_p: float, k: float = 0.25) -> Dict[str, float]:
    """
    Calculate optimal stake using Kelly criterion
    
    Args:
        edge: Betting edge as decimal (e.g., 0.03 for 3%)
        fair_p: True probability of outcome
        k: Kelly fraction (default 0.25 for conservative approach)
    
    Returns:
        Dictionary with stake percentage and recommendation
    """
    # Kelly formula: f* = (bp - q) / b
    # Where b = odds - 1, p = probability, q = 1 - p
    
    # Convert edge to implied odds
    implied_odds = 1 / fair_p
    book_odds = implied_odds / (1 + edge)
    
    b = book_odds - 1  # Decimal odds minus 1
    q = 1 - fair_p       # Probability of losing
    
    # Full Kelly stake
    kelly_full = (b * fair_p - q) / b if b != 0 else 0
    
    # Apply Kelly fraction (conservative approach)
    kelly_stake = kelly_full * k
    
    # Ensure stake is reasonable (0-10% of bankroll)
    kelly_stake = max(0, min(kelly_stake, 0.10))
    
    return {
        'kelly_percentage': round(kelly_stake * 100, 2),
        'stake_recommendation': f"{round(kelly_stake * 100, 2)}% of bankroll",
        'full_kelly': round(kelly_full * 100, 2),
        'edge': round(edge * 100, 2)
    }

def update_live(minute: int, score: str, cards: str, corners: str, 
                initial_probs: Dict[str, float] = None) -> Dict[str, float]:
    """
    Update match probabilities based on live game state
    
    Args:
        minute: Current minute in match
        score: Current score "home-away" (e.g., "1-1")
        cards: Card situation "home-away" (e.g., "1-2")
        corners: Corner count "home-away" (e.g., "5-3")
        initial_probs: Initial probabilities if available
    
    Returns:
        Updated probabilities and betting recommendations
    """
    # Parse inputs
    home_score, away_score = map(int, score.split('-'))
    home_cards, away_cards = map(int, cards.split('-'))
    home_corners, away_corners = map(int, corners.split('-'))
    
    # Base adjustments
    goal_diff = home_score - away_score
    card_diff = home_cards - away_cards
    corner_diff = home_corners - away_corners
    
    # Time factor (more weight to events as match progresses)
    time_factor = minute / 90
    
    # Goal impact (exponential based on time)
    goal_impact = goal_diff * (1 + time_factor)
    
    # Card impact (red cards worth ~0.5 goals)
    card_impact = card_diff * 0.5 * (1 - time_factor)
    
    # Corner impact (minor, more indicative of pressure)
    corner_impact = corner_diff * 0.1
    
    # Calculate live goal expectancy
    base_goals = 2.5  # Average goals per match
    live_goals = base_goals * (1 - time_factor) + abs(goal_diff)
    
    # Next goal probability (simplified Poisson)
    if minute < 75:  # Before typical late goals
        next_goal_prob = 0.25 * (1 - time_factor)
    else:
        next_goal_prob = 0.15 * (1 - time_factor)
    
    # Adjust for current state
    if goal_diff == 0:  # Draw
        next_home_prob = 0.35 + card_impact * 0.1
        next_away_prob = 0.35 - card_impact * 0.1
        next_draw_prob = 0.30
    elif goal_diff > 0:  # Home leading
        next_home_prob = 0.25 + goal_diff * 0.05
        next_away_prob = 0.45 - goal_diff * 0.05
        next_draw_prob = 0.30
    else:  # Away leading
        next_home_prob = 0.45 + goal_diff * 0.05
        next_away_prob = 0.25 - goal_diff * 0.05
        next_draw_prob = 0.30
    
    # Normalize probabilities
    total = next_home_prob + next_away_prob + next_draw_prob
    next_home_prob /= total
    next_away_prob /= total
    next_draw_prob /= total
    
    # Under/Over calculations
    current_goals = home_score + away_score
    
    # Probability of under 2.5 goals
    if current_goals >= 3:
        under_25_prob = 0.0
    else:
        remaining_goals_exp = live_goals * (1 - time_factor)
        under_25_prob = math.exp(-remaining_goals_exp)
    
    over_25_prob = 1 - under_25_prob
    
    return {
        'current_state': {
            'minute': minute,
            'score': score,
            'goal_difference': goal_diff,
            'cards': cards,
            'corners': corners
        },
        'next_goal_probabilities': {
            'home': round(next_home_prob, 3),
            'away': round(next_away_prob, 3),
            'draw': round(next_draw_prob, 3)
        },
        'total_goals': {
            'under_2.5': round(under_25_prob, 3),
            'over_2.5': round(over_25_prob, 3)
        },
        'live_goals_expectancy': round(live_goals, 2)
    }

def calculate_edge(fair_odds: float, book_odds: float) -> float:
    """
    Calculate betting edge
    
    Args:
        fair_odds: Calculated fair odds
        book_odds: Bookmaker odds
    
    Returns:
        Edge as decimal (positive = value bet)
    """
    return (fair_odds - book_odds) / book_odds

def format_bet_recommendation(league: str, home_team: str, away_team: str,
                            selection: str, book_odds: float, fair_odds: float,
                            edge: float, kelly_pct: float, bankroll: float = 10000) -> str:
    """
    Format betting recommendation in standard format
    """
    stake_amount = (kelly_pct / 100) * bankroll
    
    return f"""🇫🇷 {league} – {home_team} vs {away_team}
Bet: {selection} @{book_odds} (fair {fair_odds}) → edge {edge:.1f}%
Kelly: {kelly_pct:.1f}% bankroll → €{stake_amount:.0f} sur {bankroll}k"""

# Example usage and testing
if __name__ == "__main__":
    # Test fair odds calculation
    print("=== Fair Odds Test ===")
    result = fair_odds(delta_xg=0.5, delta_ranking=2.0, delta_days=-1.0)
    print(json.dumps(result, indent=2))
    
    # Test Kelly calculation
    print("\n=== Kelly Test ===")
    kelly_result = kelly(edge=0.068, fair_p=0.54)  # 6.8% edge, 54% probability
    print(json.dumps(kelly_result, indent=2))
    
    # Test live update
    print("\n=== Live Update Test ===")
    live_result = update_live(minute=67, score="1-1", cards="0-1", corners="5-3")
    print(json.dumps(live_result, indent=2))
    
    # Test edge calculation
    print("\n=== Edge Test ===")
    edge = calculate_edge(fair_odds=1.85, book_odds=2.10)
    print(f"Edge: {edge:.3f} ({edge*100:.1f}%)")
    
    # Test bet formatting
    print("\n=== Bet Format Test ===")
    bet_text = format_bet_recommendation(
        league="Ligue 1", home_team="PSG", away_team="Lorient",
        selection="PSG", book_odds=2.10, fair_odds=1.85,
        edge=6.8, kelly_pct=2.1, bankroll=10
    )
    print(bet_text)