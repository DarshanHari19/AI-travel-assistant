#!/usr/bin/env python3
"""
Pre-flight Check Script
Verifies that all requirements are met before running the agent
"""

import os
import sys
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_path = Path(".env")
    
    if not env_path.exists():
        return False, ".env file not found"
    
    with open(env_path) as f:
        content = f.read()
    
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API key",
        "OPENWEATHER_API_KEY": "OpenWeatherMap API key"
    }
    
    missing = []
    placeholder = []
    
    for var, desc in required_vars.items():
        if var not in content:
            missing.append(f"{var} ({desc})")
        elif "your_" in content or "your-" in content:
            # Check if still has placeholder values
            for line in content.split('\n'):
                if var in line and ('your_' in line or 'your-' in line):
                    placeholder.append(f"{var} ({desc})")
                    break
    
    if missing:
        return False, f"Missing variables: {', '.join(missing)}"
    
    if placeholder:
        return False, f"Please update placeholder values: {', '.join(placeholder)}"
    
    return True, "All environment variables configured"


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        return False, f"Python 3.10+ required (found {version.major}.{version.minor})"
    return True, f"Python {version.major}.{version.minor}.{version.micro}"


def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        ("fastapi", "FastAPI"),
        ("pydantic", "Pydantic"),
        ("httpx", "httpx"),
        ("langchain", "LangChain"),
        ("langchain_openai", "LangChain OpenAI"),
        ("openai", "OpenAI"),
    ]
    
    missing = []
    installed = []
    
    for package, name in required_packages:
        try:
            __import__(package)
            installed.append(name)
        except ImportError:
            missing.append(name)
    
    if missing:
        return False, f"Missing packages: {', '.join(missing)}"
    
    return True, f"All {len(installed)} required packages installed"


def check_mcp_server():
    """Check if MCP server files exist"""
    server_path = Path("../mcp-server/server.py")
    
    if not server_path.exists():
        return False, "MCP server file not found"
    
    return True, "MCP server files present"


def check_api_keys():
    """Verify API keys are set in environment"""
    openai_key = os.getenv("OPENAI_API_KEY")
    weather_key = os.getenv("OPENWEATHER_API_KEY")
    
    issues = []
    
    if not openai_key:
        issues.append("OPENAI_API_KEY not in environment")
    elif openai_key.startswith("your_") or openai_key.startswith("your-"):
        issues.append("OPENAI_API_KEY has placeholder value")
    elif len(openai_key) < 20:
        issues.append("OPENAI_API_KEY seems too short")
    
    if not weather_key:
        issues.append("OPENWEATHER_API_KEY not in environment")
    elif weather_key.startswith("your_") or weather_key.startswith("your-"):
        issues.append("OPENWEATHER_API_KEY has placeholder value")
    elif len(weather_key) < 20:
        issues.append("OPENWEATHER_API_KEY seems too short")
    
    if issues:
        return False, "; ".join(issues)
    
    return True, "API keys are configured"


def print_status(check_name, passed, message):
    """Print formatted status message"""
    status = "✅" if passed else "❌"
    print(f"{status} {check_name:30} {message}")


def main():
    """Run all pre-flight checks"""
    print("\n" + "="*70)
    print("  Strategic Business Travel Assistant - Pre-flight Check")
    print("="*70 + "\n")
    
    # Load .env file if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️  python-dotenv not installed, skipping .env loading\n")
    
    checks = [
        ("Python Version", check_python_version),
        (".env File", check_env_file),
        ("API Keys", check_api_keys),
        ("Python Packages", check_dependencies),
        ("MCP Server Files", check_mcp_server),
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            passed, message = check_func()
            results.append(passed)
            print_status(name, passed, message)
        except Exception as e:
            results.append(False)
            print_status(name, False, f"Error: {str(e)}")
    
    print("\n" + "="*70)
    
    if all(results):
        print("✅ All checks passed! You're ready to run the agent.")
        print("\nTo start the agent:")
        print("  python agent.py")
        print("\nTo test the agent:")
        print("  python test_agent.py --mode interactive")
        print("="*70 + "\n")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Create .env file: cp .env.example .env")
        print("  3. Add your API keys to the .env file")
        print("  4. Make sure you're in the backend-agent directory")
        print("="*70 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
