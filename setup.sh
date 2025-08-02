#!/bin/bash

# D&D RAG Chunker Setup Script
# This script sets up the Python environment and installs dependencies

echo "🏗️  Setting up D&D RAG Chunker Environment"
echo "=========================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "To use the chunker:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Set your OpenAI API key: export OPENAI_API_KEY='your-key-here'"
echo "3. Run the chunker: python dnd_rag_chunker_enhanced.py"
echo ""
echo "For a dry run (no vector store creation): python dnd_rag_chunker_enhanced.py --dry-run"
echo "To use a custom config: python dnd_rag_chunker_enhanced.py --config my_config.ini"
echo ""
