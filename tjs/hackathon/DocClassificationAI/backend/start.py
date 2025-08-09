#!/usr/bin/env python3
"""
Startup script for VA Document Classification System
"""

import os
import sys
import subprocess
from pathlib import Path

def check_tesseract():
    """Check if Tesseract is installed."""
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Tesseract is installed")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ Tesseract is not installed or not in PATH")
    print("Please install Tesseract:")
    print("  macOS: brew install tesseract")
    print("  Ubuntu: sudo apt-get install tesseract-ocr")
    print("  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
    return False

def check_env_file():
    """Check if .env file exists."""
    env_path = Path(".env")
    if env_path.exists():
        print("✅ .env file found")
        return True
    else:
        print("❌ .env file not found")
        print("Please create .env file from env_example.txt")
        return False

def check_dependencies():
    """Check if required Python packages are installed."""
    required_packages = [
        ('fastapi', 'fastapi'), 
        ('uvicorn', 'uvicorn'), 
        ('pytesseract', 'pytesseract'), 
        ('pdf2image', 'pdf2image'), 
        ('Pillow', 'PIL'), 
        ('google-generativeai', 'google.generativeai'),  # Default provider
        ('groq', 'groq'), 
        ('openai', 'openai'), 
        ('python-dotenv', 'dotenv')
    ]
    
    missing_packages = []
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Please install dependencies: pip install -r requirements.txt")
        return False
    else:
        print("✅ All required packages are installed")
        return True

def create_directories():
    """Create necessary directories."""
    directories = [
        "data/uploads",
        "data/sorted",
        "data/review", 
        "data/rejected"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Data directories created")

def main():
    """Main startup function."""
    print("🚀 VA Document Classification System Startup")
    print("=" * 50)
    
    # Check prerequisites
    checks_passed = True
    
    if not check_tesseract():
        checks_passed = False
    
    if not check_env_file():
        checks_passed = False
    
    if not check_dependencies():
        checks_passed = False
    
    if not checks_passed:
        print("\n❌ Prerequisites not met. Please fix the issues above.")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    print("\n✅ All checks passed!")
    print("\n🚀 Starting the server...")
    print("📖 API Documentation will be available at: http://localhost:8000/docs")
    print("🔄 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Start the server
    try:
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 