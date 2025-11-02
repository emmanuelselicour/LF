# 🎯 GPT-Bet.Foot

Système d'intelligence artificielle pour l'analyse quantitative des paris sportifs, déployé sur Render.

## 🚀 Déploiement Rapide

1. **Forkez ce repository** sur GitHub
2. **Allez sur [Render.com](https://render.com)**
3. **Connectez votre compte GitHub**
4. **Créez un nouveau Web Service**
5. **Sélectionnez ce repository**
6. **Configurez les paramètres :**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
7. **Ajoutez la variable d'environnement :**
   - `OPENAI_API_KEY` = votre clé OpenAI
8. **Déployez !**

## 📊 Utilisation

1. **Accédez à votre URL Render** (ex: `https://gpt-bet-foot.onrender.com`)
2. **Entrez les données d'un match** dans le format requis
3. **Uploader un screenshot** des cotes (optionnel)
4. **Obtenez l'analyse IA** avec recommandation de pari

## 🔧 Configuration

Modifiez la clé OpenAI dans `app.py` ligne 16 :

```python
client = openai.OpenAI(api_key="votre_nouvelle_clef_ici")
