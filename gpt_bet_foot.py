import openai
import pandas as pd
import numpy as np
import json
import base64
import time
import matplotlib.pyplot as plt
from datetime import datetime
import re

# Configuration OpenAI
client = openai.OpenAI(api_key="your_api_key_here")

class GPTBetFoot:
    def __init__(self, bankroll=10000):
        self.bankroll = bankroll
        self.trades = []
        self.vector_stores = {}
        
    def parse_text_file(self, file_path):
        """Parse les fichiers texte bruts"""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Extraction des données structurées
        data = {
            'teams': re.findall(r'([A-Za-z\s]+)\s+vs\s+([A-Za-z\s]+)', content),
            'odds': re.findall(r'(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)', content),
            'xg': re.findall(r'xg_([a-z]+):\s*(\d+\.\d+)', content),
            'ranking': re.findall(r'classement_([a-z]+):\s*(\d+)', content),
            'form': re.findall(r'forme_([a-z]+):\s*([★☆]+)', content)
        }
        return data
    
    def ocr_odds_from_image(self, image_path):
        """OCR des screenshots de cotes via GPT-4 Vision"""
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": "Extrait le tableau de cotes avec structure JSON : équipe domicile, équipe extérieure, cote victoire domicile, cote nul, cote victoire extérieure. Format : {'home_team': '', 'away_team': '', 'odds_home': X.XX, 'odds_draw': X.XX, 'odds_away': X.XX}"
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
        
        # Extraction JSON de la réponse
        try:
            odds_data = json.loads(response.choices[0].message.content)
            return odds_data
        except:
            # Fallback parsing manuel
            text = response.choices[0].message.content
            return self._parse_odds_from_text(text)
    
    def _parse_odds_from_text(self, text):
        """Parsing de secours pour les cotes"""
        odds_pattern = r'(\d+\.\d{2})'
        odds = re.findall(odds_pattern, text)
        
        if len(odds) >= 3:
            return {
                'odds_home': float(odds[0]),
                'odds_draw': float(odds[1]), 
                'odds_away': float(odds[2])
            }
        return None

    def calculate_fair_odds(self, data):
        """Calcule les cotes fair via modèle bayésien"""
        # Extraction features
        xg_home = float(data['xg'][0][1]) if data['xg'] else 1.5
        xg_away = float(data['xg'][1][1]) if len(data['xg']) > 1 else 1.0
        
        rank_home = int(data['ranking'][0][1]) if data['ranking'] else 8
        rank_away = int(data['ranking'][1][1]) if len(data['ranking']) > 1 else 12
        
        # Conversion forme étoiles en score (★ = 0.2)
        form_home = data['form'][0][1].count('★') * 0.2 if data['form'] else 0.6
        form_away = data['form'][1][1].count('★') * 0.2 if len(data['form']) > 1 else 0.4
        
        # Calcul deltas
        delta_xg = xg_home - xg_away
        delta_rank = (20 - rank_home) - (20 - rank_away)  # Inversion ranking
        delta_form = form_home - form_away
        
        # Modèle bayésien simplifié
        score = 0.3 * delta_xg + 0.2 * delta_rank + 0.1 * delta_form
        
        # Probabilités logistiques
        p_home = 1 / (1 + np.exp(-score))
        p_draw = 0.25 * (1 - abs(p_home - (1 - p_home)))  # Plus de nuls quand équipes égales
        p_away = 1 - p_home - p_draw
        
        # Normalisation
        total = p_home + p_draw + p_away
        p_home /= total
        p_draw /= total 
        p_away /= total
        
        # Cotes fair avec marge 5.5%
        margin = 0.945
        fair_odds = {
            'home': round(1 / (p_home * margin), 2),
            'draw': round(1 / (p_draw * margin), 2),
            'away': round(1 / (p_away * margin), 2)
        }
        
        return {
            'probabilities': {'home': p_home, 'draw': p_draw, 'away': p_away},
            'fair_odds': fair_odds,
            'confidence': min(0.95, abs(score) * 2)  # Confiance basée sur force prédiction
        }

    def calculate_edge(self, fair_odds, book_odds):
        """Calcule l'edge pour chaque marché"""
        edges = {}
        for market in ['home', 'draw', 'away']:
            if fair_odds[market] > book_odds[market]:
                edge = (fair_odds[market] - book_odds[market]) / book_odds[market]
                edges[market] = round(edge * 100, 2)
            else:
                edges[market] = 0.0
                
        return edges

    def kelly_criterion(self, edge, fair_prob, k_factor=0.25):
        """Calcule la stake Kelly"""
        if edge <= 0.02:  # Edge minimum 2%
            return 0
            
        # Odd fair implicite
        fair_odd = 1 / fair_prob
        
        # Fraction Kelly standard
        kelly_frac = edge / (fair_odd - 1)
        
        # Kelly fractionnée pour contrôle risque
        kelly_frac = kelly_frac * k_factor
        
        # Plafonnement à 5%
        kelly_frac = min(kelly_frac, 0.05)
        
        stake = self.bankroll * kelly_frac
        return round(stake, 2)

    def analyze_match(self, text_file, image_file=None):
        """Pipeline complet d'analyse d'un match"""
        print("🔍 Analyse du match en cours...")
        
        # Parsing données
        data = self.parse_text_file(text_file)
        
        if image_file:
            book_odds = self.ocr_odds_from_image(image_file)
        else:
            # Fallback aux cotes du fichier texte
            odds = data['odds'][0] if data['odds'] else ['1.80', '3.50', '4.20']
            book_odds = {
                'odds_home': float(odds[0]),
                'odds_draw': float(odds[1]),
                'odds_away': float(odds[2])
            }
        
        # Calcul cotes fair
        fair_data = self.calculate_fair_odds(data)
        
        # Conversion format book_odds
        book_odds_dict = {
            'home': book_odds['odds_home'],
            'draw': book_odds['odds_draw'],
            'away': book_odds['odds_away']
        }
        
        # Calcul edges
        edges = self.calculate_edge(fair_data['fair_odds'], book_odds_dict)
        
        # Recherche meilleur edge
        best_market = max(edges.items(), key=lambda x: x[1])
        
        if best_market[1] >= 3.0:  # Seuil edge 3%
            stake = self.kelly_criterion(
                best_market[1] / 100, 
                fair_data['probabilities'][best_market[0]]
            )
            
            recommendation = {
                'match': f"{data['teams'][0][0]} vs {data['teams'][0][1]}",
                'bet': best_market[0],
                'odds': book_odds_dict[best_market[0]],
                'fair_odds': fair_data['fair_odds'][best_market[0]],
                'edge': best_market[1],
                'stake': stake,
                'confidence': fair_data['confidence'],
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return recommendation
        else:
            return {'action': 'NO_BET', 'max_edge': best_market[1]}

    def execute_trade(self, recommendation):
        """Exécute un trade papier"""
        if recommendation['action'] == 'NO_BET':
            print("❌ Pas d'opportunité (edge < 3%)")
            return
            
        trade_id = f"TRADE_{len(self.trades) + 1:04d}"
        trade = {
            'id': trade_id,
            **recommendation,
            'bankroll_before': self.bankroll
        }
        
        # Simulation résultat (à remplacer par résultat réel)
        # Pour le papier trading, on simule avec 55% de win rate
        import random
        win = random.random() < 0.55
        
        if win:
            trade['result'] = 'WIN'
            trade['profit'] = recommendation['stake'] * (recommendation['odds'] - 1)
            self.bankroll += trade['profit']
        else:
            trade['result'] = 'LOSE' 
            trade['profit'] = -recommendation['stake']
            self.bankroll += trade['profit']
            
        trade['bankroll_after'] = self.bankroll
        self.trades.append(trade)
        
        print(f"✅ {trade_id}: {trade['result']} | Profit: {trade['profit']:.2f}€ | Bankroll: {self.bankroll:.2f}€")
        return trade

    def generate_report(self):
        """Génère le rapport de performance"""
        if not self.trades:
            print("Aucun trade à analyser")
            return
            
        df = pd.DataFrame(self.trades)
        
        # Métriques de performance
        total_trades = len(df)
        winning_trades = len(df[df['result'] == 'WIN'])
        win_rate = winning_trades / total_trades
        
        total_staked = df['stake'].sum()
        total_profit = df['profit'].sum()
        roi = (total_profit / total_staked) * 100
        
        # Drawdown
        df['cumulative_profit'] = df['profit'].cumsum()
        df['peak'] = df['cumulative_profit'].cummax()
        df['drawdown'] = df['cumulative_profit'] - df['peak']
        max_drawdown = df['drawdown'].min()
        
        print("\n📊 RAPPORT DE PERFORMANCE")
        print("=" * 50)
        print(f"Total Trades: {total_trades}")
        print(f"Win Rate: {win_rate:.1%}")
        print(f"ROI: {roi:.2f}%")
        print(f"Bankroll Finale: {self.bankroll:.2f}€")
        print(f"Max Drawdown: {max_drawdown:.2f}€")
        print(f"Profit Total: {total_profit:.2f}€")
        
        # Graphique
        plt.figure(figsize=(12, 6))
        plt.plot(df['cumulative_profit'], label='Profit Cumulé')
        plt.fill_between(df.index, df['drawdown'], alpha=0.3, color='red', label='Drawdown')
        plt.title('Évolution de la Bankroll - GPT-Bet.Foot')
        plt.xlabel('Nombre de Trades')
        plt.ylabel('Profit (€)')
        plt.legend()
        plt.grid(True)
        plt.savefig('bankroll_evolution.png')
        plt.show()
        
        return df

# 🎯 SCRIPT D'UTILISATION
if __name__ == "__main__":
    # Initialisation bot
    bot = GPTBetFoot(bankroll=10000)
    
    print("🎯 GPT-Bet.Foot Activé")
    print(f"Bankroll Initiale: {bot.bankroll}€")
    
    # Exemple d'analyse
    try:
        # Remplacez par vos fichiers réels
        result = bot.analyze_match(
            text_file="exemple_match.txt", 
            image_file="cotes_screenshot.jpg"
        )
        
        print("\n📈 RECOMMANDATION:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if 'action' not in result:
            # Exécution du trade
            trade = bot.execute_trade(result)
            
            # Génération rapport
            if len(bot.trades) >= 5:  # Après 5 trades
                bot.generate_report()
                
    except Exception as e:
        print(f"❌ Erreur: {e}")
