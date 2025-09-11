#!/bin/bash

# Swiss Energy Scenarios Decipher System - Installation Script

echo "🇨🇭 Swiss Energy Scenarios Decipher System - Installation"
echo "========================================================"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8+ and try again."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "🔧 Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📦 Installing required packages..."
pip install -r requirements.txt

echo ""
echo "✅ Installation complete!"
echo ""
echo "🚀 To run the application:"
echo ""
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Configure your OpenAI API key in .env file"
echo ""
echo "3. Run the CLI interface:"
echo "   python main.py"
echo ""
echo "4. Or run the web interface:"
echo "   streamlit run streamlit_app.py"
echo ""
echo "5. Test the system:"
echo "   python test_system.py"
echo ""
echo "Happy analyzing! 🇨🇭"