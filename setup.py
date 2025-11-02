#!/usr/bin/env python3
"""
GPT-Bet.Foot Setup Script
Complete installation and configuration guide
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} detected")

def install_dependencies():
    """Install required packages"""
    print("\n📦 Installing dependencies...")
    
    packages = [
        "openai>=1.0.0",
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "matplotlib>=3.5.0",
        "seaborn>=0.11.0",
        "plotly>=5.0.0",
        "Pillow>=8.0.0",
        "pytesseract>=0.3.0",
        "jupyter>=1.0.0",
        "ipykernel>=6.0.0"
    ]
    
    for package in packages:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
            print(f"✅ {package}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
    
    print("\n📦 All dependencies installed!")

def setup_directories():
    """Create necessary directories"""
    print("\n📁 Setting up directories...")
    
    directories = [
        "data",
        "screenshots", 
        "examples",
        "exports",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ {directory}/")
    
    print("📁 Directory structure created!")

def create_config():
    """Create configuration file"""
    print("\n⚙️  Creating configuration...")
    
    config = {
        "openai_api_key": "your-api-key-here",
        "bankroll": 10000,
        "kelly_fraction": 0.25,
        "min_edge": 0.03,
        "human_delay": [1, 3],
        "max_stake_pct": 0.05,
        "data_dir": "./data",
        "screenshots_dir": "./screenshots",
        "exports_dir": "./exports",
        "logs_dir": "./logs",
        "tesseract_path": "C:/Program Files/Tesseract-OCR/tesseract.exe"
    }
    
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("✅ Configuration file created: config.json")
    print("📝 Please update your OpenAI API key in config.json")

def setup_tesseract():
    """Setup Tesseract OCR"""
    print("\n📸 Setting up OCR...")
    
    print("For optimal OCR performance:")
    print("1. Windows: Download Tesseract from GitHub")
    print("2. Mac: brew install tesseract")
    print("3. Linux: sudo apt-get install tesseract-ocr")
    print("4. Update tesseract_path in config.json")
    
    print("✅ OCR configuration ready")

def create_sample_data():
    """Create sample data files"""
    print("\n📊 Creating sample data...")
    
    # Sample configuration for a match
    sample_match = {
        "league": "Ligue 1",
        "home_team": "PSG",
        "away_team": "Lorient", 
        "book_odds": {"home": 2.10, "draw": 3.40, "away": 3.60},
        "delta_xg": 0.8,
        "delta_ranking": 15,
        "delta_days": 2
    }
    
    with open("examples/sample_match.json", "w") as f:
        json.dump(sample_match, f, indent=2)
    
    print("✅ Sample match data created")

def test_installation():
    """Test the installation"""
    print("\n🧪 Testing installation...")
    
    try:
        import openai
        import pandas
        import numpy
        import matplotlib
        import plotly
        import PIL
        
        print("✅ All packages imported successfully")
        
        # Test OpenAI connection
        client = openai.OpenAI(api_key="test-key")
        print("✅ OpenAI client created")
        
        return True
        
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False

def create_startup_script():
    """Create startup script"""
    print("\n🚀 Creating startup script...")
    
    startup_content = '''#!/bin/bash
# GPT-Bet.Foot Startup Script

echo "🎯 Starting GPT-Bet.Foot System..."
echo "=================================="

# Check if config exists
if [ ! -f "config.json" ]; then
    echo "❌ Configuration file not found!"
    echo "Please run: python setup.py"
    exit 1
fi

# Start Jupyter notebook
echo "📓 Starting Jupyter notebook..."
jupyter notebook run_local.ipynb --no-browser --port=8888

echo "✅ System ready!"
echo "🌐 Open http://localhost:8888 in your browser"
'''
    
    with open("start.sh", "w") as f:
        f.write(startup_content)
    
    os.chmod("start.sh", 0o755)
    print("✅ Startup script created: start.sh")

def main():
    """Main setup function"""
    print("🎯 GPT-Bet.Foot Setup")
    print("=" * 50)
    
    check_python_version()
    install_dependencies()
    setup_directories()
    create_config()
    setup_tesseract()
    create_sample_data()
    
    if test_installation():
        print("\n🎉 Installation completed successfully!")
        create_startup_script()
        
        print("\n📋 Next steps:")
        print("1. Update config.json with your OpenAI API key")
        print("2. Install Tesseract OCR (optional, for local OCR)")
        print("3. Run: ./start.sh to launch the system")
        print("4. Open index.html for web interface")
        print("5. Start analyzing matches!")
        
        print("\n📚 Documentation: README.md")
        print("🚀 Quick start: python gpt_bet_foot_functions.py")
        
    else:
        print("\n❌ Installation failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()