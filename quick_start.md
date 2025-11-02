# GPT-Bet.Foot Quick Start Guide ⚡

Get up and running with GPT-Bet.Foot in under 5 minutes!

## 🚀 Instant Setup

### 1. Install & Configure
```bash
# Clone and setup
python setup.py

# Enter your OpenAI API key when prompted
# System will install all dependencies automatically
```

### 2. Launch System
```bash
# Option A: Jupyter Notebook (Recommended)
jupyter notebook run_local.ipynb

# Option B: Web Interface
open index.html in your browser

# Option C: Command Line
python gpt_bet_foot_functions.py
```

### 3. Your First Bet Analysis

```python
# Quick analysis function
quick_analyze('Ligue 1', 'PSG', 'Lorient', 2.10, 3.40, 3.60, 0.8, 15, 2)

# Expected output:
# 🇫🇷 Ligue 1 – PSG vs Lorient
# Bet: PSG @2.10 (fair 1.85) → edge +6.8%
# Kelly: 2.1% bankroll → €210 sur 10k
```

## 📋 Daily Workflow

### Morning Routine (5 minutes)
1. **Check overnight results**
   ```python
   show_performance()
   ```

2. **Upload new data**
   - Screenshot odds from bookmaker sites
   - Upload CSV with match statistics
   - Add injury reports (PDF/TXT)

3. **Run analysis**
   ```python
   # Process screenshots
   odds = extract_odds_from_screenshot('screenshot.png')
   
   # Analyze all matches
   results = batch_analyze_matches(data)
   ```

### Match Day (2 minutes per match)
1. **Input match details**
2. **Get AI recommendations**
3. **Place paper trades**
4. **Monitor live updates**

### Evening Review (3 minutes)
1. **Settle completed bets**
   ```python
   settle('match_id', 'Home', 'WIN')
   ```

2. **Generate performance report**
   ```python
   visualizer.generate_performance_report()
   ```

3. **Export data for records**
   ```python
   export_trades()
   ```

## 🎯 Key Commands

### Analysis Commands
```python
# Single match analysis
quick_analyze(league, home, away, h_odds, d_odds, a_odds, xg_diff, rank_diff, days_diff)

# Batch analysis
batch_analyze_from_csv('odds_data.csv')

# Live match updates
update_live(minute=67, score="1-1", cards="0-1", corners="5-3")
```

### Management Commands
```python
# Show performance
show_performance()

# Settle bets
settle(match_id, selection, result)

# Bankroll status
print(f"Current bankroll: €{paper_trader.bankroll}")

# Export data
export_trades()
```

### OCR Commands
```python
# Extract from screenshot
odds = odds_ocr.extract_odds('screenshot.png')

# Process multiple screenshots
batch_process_screenshots('screenshots/')
```

## 📊 Understanding the Output

### Bet Recommendation Format
```
🇫🇷 Ligue 1 – PSG vs Lorient
Bet: PSG @2.10 (fair 1.85) → edge +6.8%
Kelly: 2.1% bankroll → €210 sur 10k
```

**What it means:**
- **Edge +6.8%**: Value found (bookmaker odds vs fair odds)
- **Kelly 2.1%**: Optimal stake percentage
- **€210**: Recommended stake on €10,000 bankroll

### Performance Metrics
```
📊 Performance Report
Total Bets: 247
Win Rate: 54.3%
ROI: +4.2%
Yield: +5.8%
CLV: +3.1%
Max Drawdown: 8.3%
```

**Target KPIs:**
- ✅ CLV > +2% (Current: +3.1%)
- ✅ Yield > +4% (Current: +5.8%) 
- ✅ Max DD < 15% (Current: 8.3%)

## 🔧 Customization

### Adjust Risk Settings
```python
# Modify in config.json
{
    "kelly_fraction": 0.25,    # Conservative approach
    "min_edge": 0.03,          # Minimum 3% edge
    "max_stake_pct": 0.05,     # Max 5% per bet
    "human_delay": [1, 3]      # Random delays
}
```

### Add New Leagues
```python
# Update league configurations
LEAGUE_CONFIGS = {
    'Ligue 1': {'avg_goals': 2.5, 'home_advantage': 0.3},
    'Premier League': {'avg_goals': 2.8, 'home_advantage': 0.4}
}
```

### Modify Bayesian Model
```python
# Adjust weights in fair_odds function
P = 1/(1+exp(-(0.3*delta_xg + 0.2*delta_ranking + 0.1*delta_days)))
# Weights: xG (30%), Ranking (20%), Rest (10%)
```

## 🎓 Pro Tips

### Maximizing Edge Detection
1. **Focus on smaller leagues** (less efficient markets)
2. **Look for team news impacts** (injuries, suspensions)
3. **Monitor line movements** (sharp money indicators)
4. **Consider situational factors** (rest days, travel)

### Bankroll Management
1. **Stick to Kelly staking** (don't override system)
2. **Track closing line value** (measure prediction quality)
3. **Review performance weekly** (identify improvements)
4. **Stay disciplined** (avoid emotional betting)

### Data Quality
1. **Use multiple data sources** (cross-validate)
2. **Update team news regularly** (injuries matter)
3. **Verify odds accuracy** (check multiple bookmakers)
4. **Maintain historical records** (for model training)

## 🚨 Common Issues & Solutions

### "No value bets found"
**Cause**: Edge too small or market efficient
**Solution**: 
- Check smaller leagues
- Look for team news impacts
- Verify odds accuracy

### "OCR not working"
**Cause**: Tesseract not installed
**Solution**:
```bash
# Windows: Download from GitHub
# Mac: brew install tesseract  
# Linux: sudo apt-get install tesseract-ocr
```

### "API rate limit"
**Cause**: Too many requests
**Solution**:
- Add delays between requests
- Batch process when possible
- Monitor API usage

### "Poor performance"
**Cause**: Model needs adjustment
**Solution**:
- Review betting history
- Adjust model parameters
- Focus on specific leagues

## 📈 Next Steps

### Week 1: Foundation
- [ ] Complete setup and configuration
- [ ] Run sample analyses
- [ ] Understand system components
- [ ] Practice with paper trading

### Week 2: Optimization  
- [ ] Collect 50+ matches of data
- [ ] Fine-tune model parameters
- [ ] Identify most profitable leagues
- [ ] Establish daily workflow

### Week 3: Scaling
- [ ] Analyze 100+ matches
- [ ] Develop custom strategies
- [ ] Build historical database
- [ ] Optimize performance

### Week 4: Mastery
- [ ] Target 250+ matches analyzed
- [ ] Achieve consistent +2% CLV
- [ ] Develop advanced techniques
- [ ] Plan for 1000 match goal

## 🎯 Success Metrics

### Daily Targets
- ✅ Analyze 5-10 matches
- ✅ Maintain +2% CLV average
- ✅ Keep detailed records
- ✅ Follow risk management rules

### Weekly Targets  
- ✅ Review performance trends
- ✅ Adjust model if needed
- ✅ Identify improvement areas
- ✅ Plan next week's focus

### Monthly Targets
- ✅ Achieve +4% yield target
- ✅ Stay under 15% max drawdown
- ✅ Complete 200+ match analysis
- ✅ Refine strategies

## 🏆 Advanced Features

### Live Trading Mode
```python
# Activate live mode (paper trading)
enable_live_mode()

# Real-time updates during matches
update_live(minute, score, cards, corners)
```

### Custom Analytics
```python
# Create custom reports
generate_custom_report(metrics=['clv', 'yield', 'max_dd'])

# Compare strategies
compare_strategies(['kelly', 'flat', 'percentage'])
```

### Batch Processing
```python
# Process entire matchday
process_matchday('fixtures.csv')

# Bulk screenshot analysis
batch_ocr_analysis('screenshots/')
```

---

## 🚀 You're Ready!

You now have everything needed to start beating the closing line with GPT-Bet.Foot. Remember:

1. **Start small** - Practice with paper trading
2. **Stay disciplined** - Follow the system rules  
3. **Track everything** - Data is your friend
4. **Keep learning** - Improve continuously

**Target: +2% CLV over 1000 matches** 🎯

Good luck, and may the odds be ever in your favor! 🤖⚽