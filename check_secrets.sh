#!/bin/bash

# GitHub Secrets Configuration Helper
# This script helps you identify which API keys to add as GitHub Secrets

echo "🔐 GitHub Secrets Setup Helper"
echo "========================================"
echo ""
echo "You need to configure these secrets in your GitHub repository:"
echo ""
echo "📍 Location: Settings → Secrets and variables → Actions → New repository secret"
echo ""

# Check if .env file exists
if [ -f "backend-agent/.env" ]; then
    echo "✓ Found .env file in backend-agent/"
    echo ""
    
    # Extract API keys from .env (without showing values)
    if grep -q "OPENWEATHER_API_KEY" backend-agent/.env; then
        echo "1️⃣  OPENWEATHER_API_KEY"
        echo "   Name: OPENWEATHER_API_KEY"
        echo "   Value: (copy from your .env file)"
        echo "   Current: $(grep OPENWEATHER_API_KEY backend-agent/.env | cut -d'=' -f1)=***"
        echo ""
    fi
    
    if grep -q "OPENAI_API_KEY" backend-agent/.env; then
        echo "2️⃣  OPENAI_API_KEY"
        echo "   Name: OPENAI_API_KEY"
        echo "   Value: (copy from your .env file)"
        echo "   Current: $(grep OPENAI_API_KEY backend-agent/.env | cut -d'=' -f1)=***"
        echo ""
    fi
    
    if grep -q "AERODATABOX_API_KEY" backend-agent/.env; then
        echo "3️⃣  AERODATABOX_API_KEY"
        echo "   Name: AERODATABOX_API_KEY"
        echo "   Value: (copy from your .env file)"
        echo "   Current: $(grep AERODATABOX_API_KEY backend-agent/.env | cut -d'=' -f1)=***"
        echo ""
    fi
else
    echo "⚠️  No .env file found in backend-agent/"
    echo ""
    echo "You need to add these secrets manually:"
    echo ""
    echo "1️⃣  OPENWEATHER_API_KEY"
    echo "   Your OpenWeather API key"
    echo ""
    echo "2️⃣  OPENAI_API_KEY"
    echo "   Your OpenAI API key (starts with sk-)"
    echo ""
    echo "3️⃣  AERODATABOX_API_KEY"
    echo "   Your RapidAPI key for AeroDataBox (for real flight data)"
    echo ""
fi

echo "========================================"
echo "📖 Step-by-Step Instructions:"
echo ""
echo "1. Go to your GitHub repository"
echo "2. Click 'Settings' (top right)"
echo "3. Click 'Secrets and variables' → 'Actions'"
echo "4. Click 'New repository secret'"
echo "5. Add each secret one by one:"
echo "   - Name: OPENWEATHER_API_KEY"
echo "   - Value: [paste your API key]"
echo "   - Click 'Add secret'"
echo "6. Repeat for OPENAI_API_KEY and AERODATABOX_API_KEY"
echo ""
echo "✅ After adding all secrets, push your code:"
echo "   git add ."
echo "   git commit -m 'Add GitHub Actions workflow'"
echo "   git push origin main"
echo ""
echo "🚀 Then check GitHub Actions tab to see tests run!"
echo "========================================"
