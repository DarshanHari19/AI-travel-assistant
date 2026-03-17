#!/bin/bash
# API Testing Examples for Strategic Business Travel Assistant
# Make sure the agent is running: python agent.py

BASE_URL="http://localhost:8000"

echo "======================================"
echo "Strategic Business Travel Assistant"
echo "API Testing Examples"
echo "======================================"
echo ""

# Check if server is running
echo "1. Health Check"
echo "   Checking if the service is running..."
echo ""
curl -s "$BASE_URL/health" | python3 -m json.tool
echo ""
echo ""

# Basic weather query
echo "2. Basic Weather Query"
echo "   Query: 'What's the weather like in London?'"
echo ""
curl -s -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the weather like in London?",
    "session_id": "example_1"
  }' | python3 -m json.tool
echo ""
echo ""

# Flight delay prediction
echo "3. Flight Delay Prediction"
echo "   Query: 'Should I be worried about flight delays to Tokyo?'"
echo ""
curl -s -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I am flying to Tokyo tomorrow. Should I be worried about flight delays?",
    "session_id": "example_2"
  }' | python3 -m json.tool
echo ""
echo ""

# Packing advice
echo "4. Packing Recommendations"
echo "   Query: 'What should I pack for New York?'"
echo ""
curl -s -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I am going to New York for 3 days. What should I pack?",
    "session_id": "example_3"
  }' | python3 -m json.tool
echo ""
echo ""

# Multi-city comparison
echo "5. Multi-City Weather Comparison"
echo "   Query: 'Compare weather in Paris and Rome'"
echo ""
curl -s -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need to choose between Paris or Rome for my trip next week. Which has better weather?",
    "session_id": "example_4"
  }' | python3 -m json.tool
echo ""
echo ""

# Travel timing advice
echo "6. Travel Timing Advice"
echo "   Query: 'Best day to travel to Seattle this week?'"
echo ""
curl -s -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "When is the best day to travel to Seattle this week considering the weather?",
    "session_id": "example_5"
  }' | python3 -m json.tool
echo ""
echo ""

# Error handling - invalid city
echo "7. Error Handling Test"
echo "   Query: Invalid city name"
echo ""
curl -s -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the weather in XYZ123?",
    "session_id": "example_6"
  }' | python3 -m json.tool
echo ""
echo ""

echo "======================================"
echo "Testing Complete!"
echo "======================================"
