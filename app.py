from flask import Flask, render_template, request, jsonify, send_file
import openai
import pandas as pd
import numpy as np
import json
import base64
import io
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import re
import os

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Configuration OpenAI
client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY', '6742012865:AAEPLQN_mianrxvljmdx6dStwb_iOS3rAQU'))

class GPTBetFoot:
    def __init__(self, bankroll=10000):
        self.bankroll = bankroll
        self.trades = []
        
    def parse_text_content(self, content):
        """Parse le contenu texte brut"""
        data = {
            'teams': re.findall(r'([A-Za-z\s]+)\s+vs\s+([A-Za-z\s]+)', content),
            'odds': re.findall(r'(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)', content),
            'xg': re.findall(r'xg_([a-z]+):\s*(\d+\.\d+)', content),
            'ranking': re.findall(r'classement_([a-z]+):\s*(\d+)', content),
            'form': re.findall(r'forme_([a-z]+):\s*([★☆]+)', content)
        }
        return data
    
    def ocr_odds_from_image(self, image_file):
        """OCR des images via GPT-4 Vision"""
        try:
            image_data = image_file.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            response = client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", 
                                "text": "Extrait les cotes sportives exactes. Retourne uniquement du JSON: {'home_team': 'nom', 'away_team': 'nom', 'odds_home': X.XX, 'odds_draw': X.XX, 'odds_away': X.XX}"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"OCR Error: {e}")
            return None

    def calculate_fair_odds(self, data):
        """Calcule les cotes fair"""
        try:
            xg_home = float(data['xg'][0][1]) if data['xg'] else 1.5
            xg_away = float(data['xg'][1][1]) if len(data['xg']) > 1 else 1.0
            
            rank_home = int(data['ranking'][0][1]) if data['ranking'] else 8
            rank_away = int(data['ranking'][1][1]) if len(data['ranking']) > 1 else 12
            
            form_home = data['form'][0][1].count('★') * 0.2 if data['form'] else 0.6
            form_away = data['form'][1][1].count('★') * 0.2 if len(data['form']) > 1 else 0.4
            
            delta_xg = xg_home - xg_away
            delta_rank = (20 - rank_home) - (20 - rank_away)
            delta_form = form_home - form_away
            
            score = 0.3 * delta_xg + 0.2 * delta_rank + 0.1 * delta_form
            
            p_home = 1 / (1 + np.exp(-score))
            p_draw = 0.25 * (1 - abs(p_home - (1 - p_home)))
            p_away = 1 - p_home - p_draw
            
            total = p_home + p_draw + p_away
            p_home /= total
            p_draw /= total 
            p_away /= total
            
            margin = 0.945
            fair_odds = {
                'home': round(1 / (p_home * margin), 2),
                'draw': round(1 / (p_draw * margin), 2),
                'away': round(1 / (p_away * margin), 2)
            }
            
            return {
                'probabilities': {
                    'home': round(p_home, 3),
                    'draw': round(p_draw, 3),
                    'away': round(p_away, 3)
                },
                'fair_odds': fair_odds,
                'confidence': min(0.95, abs(score) * 2)
            }
        except Exception as e:
            return {'error': str(e)}

    def calculate_edge(self, fair_odds, book_odds):
        """Calcule l'edge"""
        edges = {}
        for market in ['home', 'draw', 'away']:
            fair_key = market
            book_key = f'odds_{market}'
            
            if fair_odds.get(fair_key) and book_odds.get(book_key):
                if fair_odds[fair_key] > book_odds[book_key]:
                    edge = (fair_odds[fair_key] - book_odds[book_key]) / book_odds[book_key]
                    edges[market] = round(edge * 100, 2)
                else:
                    edges[market] = 0.0
        return edges

    def kelly_criterion(self, edge, fair_prob, k_factor=0.25):
        """Calcule la stake Kelly"""
        if edge <= 0.02:
            return 0
            
        fair_odd = 1 / fair_prob
        kelly_frac = edge / (fair_odd - 1)
        kelly_frac = kelly_frac * k_factor
        kelly_frac = min(kelly_frac, 0.05)
        
        stake = self.bankroll * kelly_frac
        return round(stake, 2)

    def analyze_match(self, text_content, image_file=None):
        """Analyse complète d'un match"""
        data = self.parse_text_content(text_content)
        
        if image_file:
            book_odds = self.ocr_odds_from_image(image_file)
        else:
            odds = data['odds'][0] if data['odds'] else ['1.80', '3.50', '4.20']
            book_odds = {
                'odds_home': float(odds[0]),
                'odds_draw': float(odds[1]),
                'odds_away': float(odds[2])
            }
        
        if not book_odds:
            return {'error': 'Impossible de lire les cotes'}
        
        fair_data = self.calculate_fair_odds(data)
        if 'error' in fair_data:
            return fair_data
        
        edges = self.calculate_edge(fair_data['fair_odds'], book_odds)
        
        if edges:
            best_market = max(edges.items(), key=lambda x: x[1])
            
            if best_market[1] >= 3.0:
                stake = self.kelly_criterion(
                    best_market[1] / 100,
                    fair_data['probabilities'][best_market[0]]
                )
                
                team_names = data['teams'][0] if data['teams'] else ('Home', 'Away')
                
                recommendation = {
                    'match': f"{team_names[0]} vs {team_names[1]}",
                    'bet': best_market[0],
                    'odds': book_odds[f'odds_{best_market[0]}'],
                    'fair_odds': fair_data['fair_odds'][best_market[0]],
                    'edge': best_market[1],
                    'stake': stake,
                    'stake_percent': round((stake / self.bankroll) * 100, 2),
                    'confidence': round(fair_data['confidence'], 2),
                    'probabilities': fair_data['probabilities'],
                    'timestamp': datetime.now().isoformat(),
                    'action': 'BET'
                }
                
                # Simulation du trade
                self.simulate_trade(recommendation)
                return recommendation
        
        return {'action': 'NO_BET', 'max_edge': best_market[1] if edges else 0}

    def simulate_trade(self, recommendation):
        """Simule l'exécution d'un trade"""
        import random
        
        trade_id = f"TRADE_{len(self.trades) + 1:04d}"
        
        # Simulation avec 55% de win rate
        win = random.random() < 0.55
        
        if win:
            profit = recommendation['stake'] * (recommendation['odds'] - 1)
            result = 'WIN'
        else:
            profit = -recommendation['stake']
            result = 'LOSE'
        
        trade = {
            'id': trade_id,
            **recommendation,
            'result': result,
            'profit': round(profit, 2),
            'bankroll_before': self.bankroll
        }
        
        self.bankroll += profit
        trade['bankroll_after'] = round(self.bankroll, 2)
        
        self.trades.append(trade)
        return trade

    def get_performance_report(self):
        """Génère un rapport de performance"""
        if not self.trades:
            return {'error': 'Aucun trade à analyser'}
        
        df = pd.DataFrame(self.trades)
        
        total_trades = len(df)
        winning_trades = len(df[df['result'] == 'WIN'])
        win_rate = winning_trades / total_trades
        
        total_staked = df['stake'].sum()
        total_profit = df['profit'].sum()
        roi = (total_profit / total_staked) * 100 if total_staked > 0 else 0
        
        # Calcul drawdown
        df['cumulative_profit'] = df['profit'].cumsum()
        df['peak'] = df['cumulative_profit'].cummax()
        df['drawdown'] = df['cumulative_profit'] - df['peak']
        max_drawdown = df['drawdown'].min()
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': round(win_rate, 3),
            'total_staked': round(total_staked, 2),
            'total_profit': round(total_profit, 2),
            'roi': round(roi, 2),
            'max_drawdown': round(max_drawdown, 2),
            'final_bankroll': round(self.bankroll, 2)
        }

# Instance globale
bot = GPTBetFoot()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        text_content = request.form.get('text_data', '')
        image_file = request.files.get('image_file')
        
        if not text_content:
            return jsonify({'error': 'Données texte requises'}), 400
        
        result = bot.analyze_match(text_content, image_file)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/trades')
def get_trades():
    return jsonify(bot.trades)

@app.route('/bankroll')
def get_bankroll():
    return jsonify({'bankroll': round(bot.bankroll, 2)})

@app.route('/performance')
def get_performance():
    report = bot.get_performance_report()
    return jsonify(report)

@app.route('/report')
def generate_report():
    if not bot.trades:
        return jsonify({'error': 'Aucun trade à analyser'})
    
    try:
        df = pd.DataFrame(bot.trades)
        
        plt.figure(figsize=(12, 8))
        
        # Graphique 1: Évolution bankroll
        plt.subplot(2, 2, 1)
        plt.plot(df['bankroll_after'], label='Bankroll', color='blue', linewidth=2)
        plt.title('Évolution de la Bankroll')
        plt.xlabel('Trade')
        plt.ylabel('Bankroll (€)')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Graphique 2: Profit cumulé
        plt.subplot(2, 2, 2)
        plt.plot(df['cumulative_profit'], label='Profit Cumulé', color='green', linewidth=2)
        plt.fill_between(df.index, df['drawdown'], alpha=0.3, color='red', label='Drawdown')
        plt.title('Profit Cumulé & Drawdown')
        plt.xlabel('Trade')
        plt.ylabel('Profit (€)')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Graphique 3: Distribution des edges
        plt.subplot(2, 2, 3)
        edges = [t['edge'] for t in bot.trades if 'edge' in t]
        plt.hist(edges, bins=15, alpha=0.7, color='orange', edgecolor='black')
        plt.title('Distribution des Edges')
        plt.xlabel('Edge (%)')
        plt.ylabel('Fréquence')
        plt.grid(True, alpha=0.3)
        
        # Graphique 4: Résultats par type de pari
        plt.subplot(2, 2, 4)
        bet_types = df['bet'].value_counts()
        plt.pie(bet_types.values, labels=bet_types.index, autopct='%1.1f%%', startangle=90)
        plt.title('Répartition des Paris')
        
        plt.tight_layout()
        
        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=100, bbox_inches='tight')
        img.seek(0)
        plt.close()
        
        return send_file(img, mimetype='image/png')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'trades_count': len(bot.trades),
        'bankroll': bot.bankroll,
        'service': 'GPT-Bet.Foot API'
    })

@app.route('/test')
def test():
    """Route de test simple"""
    return jsonify({
        'message': 'GPT-Bet.Foot est opérationnel!',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
