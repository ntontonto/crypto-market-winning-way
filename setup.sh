#!/bin/bash
# ========================================
# Crypto Market Winning Way - Setup Script (Bash)
# ========================================

set -e  # Exit on error

echo ""
echo "[Setup] Starting environment setup..."
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Check if Python 3.11 is available
echo "[Setup] Checking Python 3.11..."
if ! command -v python3.11 &> /dev/null; then
    if ! py -3.11 --version &> /dev/null; then
        echo "[ERROR] Python 3.11 not found!"
        echo "[ERROR] Please install Python 3.11"
        exit 1
    fi
    PYTHON_CMD="py -3.11"
else
    PYTHON_CMD="python3.11"
fi

echo "[Setup] Python 3.11 found."
$PYTHON_CMD --version

# Remove existing .venv if it exists
if [ -d ".venv" ]; then
    echo "[Setup] Removing existing .venv..."
    rm -rf .venv
fi

# Create new virtual environment with Python 3.11
echo "[Setup] Creating virtual environment with Python 3.11..."
$PYTHON_CMD -m venv .venv

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    VENV_PYTHON="python"
elif [ -f ".venv/Scripts/python.exe" ]; then
    VENV_PYTHON=".venv/Scripts/python.exe"
else
    echo "[ERROR] Failed to create virtual environment!"
    exit 1
fi

# Upgrade pip
echo ""
echo "[Setup] Upgrading pip..."
$VENV_PYTHON -m pip install -U pip

# Install av first (prebuilt binary)
echo ""
echo "[Setup] Installing av (prebuilt binary)..."
$VENV_PYTHON -m pip install "av>=13.0.0,<14.0.0" --only-binary av || echo "[WARNING] Failed to install prebuilt av, will try from requirements.txt..."

# Install all requirements
echo ""
echo "[Setup] Installing requirements..."
$VENV_PYTHON -m pip install -r requirements.txt

# Verify manim installation
echo ""
echo "[Setup] Verifying manim installation..."
$VENV_PYTHON -m manim --version

echo ""
echo "========================================"
echo "[SUCCESS] Setup completed successfully!"
echo "========================================"
echo ""
echo "Python version:"
$VENV_PYTHON --version
echo ""
echo "Manim version:"
$VENV_PYTHON -m manim --version
echo ""
echo "You can now run: ./run_pipeline.py or run_pipeline.bat"
echo ""
