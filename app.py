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
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file

# Configuration OpenAI
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

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
        # Convertir l'image en base64
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
        
        try:
            return json.loads(response.choices[0].message.content)
        except:
            # Fallback parsing
            text = response.choices[0].message.content
            odds = re.findall(r'(\d+\.\d{2})', text)
            if len(odds) >= 3:
                return {
                    'odds_home': float(odds[0]),
                    'odds_draw': float(odds[1]),
                    'odds_away': float(odds[2])
                }
            return None

    def calculate_fair_odds(self, data):
        """Calcule les cotes fair"""
        try:
            # Extraction des données avec valeurs par défaut
            xg_home = float(data['xg'][0][1]) if data['xg'] else 1.5
            xg_away = float(data['xg'][1][1]) if len(data['xg']) > 1 else 1.0
            
            rank_home = int(data['ranking'][0][1]) if data['ranking'] else 8
            rank_away = int(data['ranking'][1][1]) if len(data['ranking']) > 1 else 12
            
            form_home = data['form'][0][1].count('★') * 0.2 if data['form'] else 0.6
            form_away = data['form'][1][1].count('★') * 0.2 if len(data['form']) > 1 else 0.4
            
            # Calcul du score
            delta_xg = xg_home - xg_away
            delta_rank = (20 - rank_home) - (20 - rank_away)
            delta_form = form_home - form_away
            
            score = 0.3 * delta_xg + 0.2 * delta_rank + 0.1 * delta_form
            
            # Probabilités
            p_home = 1 / (1 + np.exp(-score))
            p_draw = 0.25 * (1 - abs(p_home - (1 - p_home)))
            p_away = 1 - p_home - p_draw
            
            # Normalisation
            total = p_home + p_draw + p_away
            p_home /= total
            p_draw /= total 
            p_away /= total
            
            # Cotes fair avec marge
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
            if fair_odds.get(market) and book_odds.get(f'odds_{market}'):
                if fair_odds[market] > book_odds[f'odds_{market}']:
                    edge = (fair_odds[market] - book_odds[f'odds_{market}']) / book_odds[f'odds_{market}']
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
        # Parsing données texte
        data = self.parse_text_content(text_content)
        
        # Récupération cotes bookmaker
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
        
        # Calcul cotes fair
        fair_data = self.calculate_fair_odds(data)
        if 'error' in fair_data:
            return fair_data
        
        # Conversion format
        book_odds_dict = {
            'home': book_odds['odds_home'],
            'draw': book_odds['odds_draw'],
            'away': book_odds['odds_away']
        }
        
        # Calcul edges
        edges = self.calculate_edge(fair_data['fair_odds'], book_odds)
        
        # Recherche meilleur edge
        if edges:
            best_market = max(edges.items(), key=lambda x: x[1])
            
            if best_market[1] >= 3.0:
                stake = self.kelly_criterion(
                    best_market[1] / 100,
                    fair_data['probabilities'][best_market[0]]
                )
                
                team_names = data['teams'][0] if data['teams'] else ('Home', 'Away')
                
                return {
                    'match': f"{team_names[0]} vs {team_names[1]}",
                    'bet': best_market[0],
                    'odds': book_odds_dict[best_market[0]],
                    'fair_odds': fair_data['fair_odds'][best_market[0]],
                    'edge': best_market[1],
                    'stake': stake,
                    'stake_percent': round((stake / self.bankroll) * 100, 2),
                    'confidence': round(fair_data['confidence'], 2),
                    'probabilities': fair_data['probabilities'],
                    'timestamp': datetime.now().isoformat(),
                    'action': 'BET'
                }
        
        return {'action': 'NO_BET', 'max_edge': best_market[1] if edges else 0}

# Instance globale
bot = GPTBetFoot()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Endpoint d'analyse de match"""
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
    """Retourne l'historique des trades"""
    return jsonify(bot.trades)

@app.route('/bankroll')
def get_bankroll():
    """Retourne la bankroll actuelle"""
    return jsonify({'bankroll': bot.bankroll})

@app.route('/report')
def generate_report():
    """Génère un rapport de performance"""
    if not bot.trades:
        return jsonify({'error': 'Aucun trade à analyser'})
    
    try:
        df = pd.DataFrame(bot.trades)
        
        # Calcul métriques
        total_trades = len(df)
        winning_trades = len(df[df['result'] == 'WIN'])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        total_staked = df['stake'].sum()
        total_profit = df['profit'].sum() if 'profit' in df.columns else 0
        roi = (total_profit / total_staked) * 100 if total_staked > 0 else 0
        
        # Génération graphique
        plt.figure(figsize=(10, 6))
        if 'cumulative_profit' in df.columns:
            plt.plot(df['cumulative_profit'], label='Profit Cumulé', linewidth=2)
            plt.fill_between(df.index, df['drawdown'], alpha=0.3, color='red', label='Drawdown')
        plt.title('Performance GPT-Bet.Foot')
        plt.xlabel('Nombre de Trades')
        plt.ylabel('Profit (€)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Sauvegarde en mémoire
        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=100, bbox_inches='tight')
        img.seek(0)
        plt.close()
        
        return send_file(img, mimetype='image/png', as_attachment=False)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check pour Render"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
