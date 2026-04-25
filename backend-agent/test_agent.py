#!/usr/bin/env python3
"""
Test script for the Strategic Business Travel Assistant
Demonstrates the agent's capabilities with example queries
"""

import asyncio
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8000"


async def send_chat_message(message: str, session_id: str = "test_session"):
    """
    Send a test message to the chat endpoint
    
    Args:
        message: The message to send
        session_id: Optional session ID
    """
    print(f"\n{'='*80}")
    print(f"USER: {message}")
    print(f"{'='*80}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/chat",
                json={"message": message, "session_id": session_id},
                timeout=60.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\nASSISTANT:\n{data['response']}\n")
            else:
                print(f"\nERROR: {response.status_code}")
                print(response.text)
                
        except httpx.ConnectError:
            print("\n❌ ERROR: Could not connect to the server.")
            print("Make sure the agent is running: python agent.py")
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")


async def check_health():
    """Check the health status of the service"""
    print("\nChecking service health...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            data = response.json()
            
            print(f"\nHealth Status: {data['status']}")
            print("\nComponents:")
            for key, value in data['components'].items():
                print(f"  - {key}: {value}")
                
        except Exception as e:
            print(f"❌ Health check failed: {str(e)}")


async def run_tests():
    """Run a suite of test queries"""
    
    # Check health first
    await check_health()
    
    # Test queries
    test_queries = [
        "What's the weather like in London?",
        "I'm traveling to Tokyo next week. Should I be worried about flight delays?",
        "I'm going to New York tomorrow. What should I pack?",
        "Check the weather in Paris and tell me the best day to travel this week.",
        "Is it a good time to fly to Seattle? I'm concerned about rain.",
    ]
    
    print("\n" + "="*80)
    print("Running Test Queries")
    print("="*80)
    
    for i, query in enumerate(test_queries, 1):
        await send_chat_message(query, session_id=f"test_session_{i}")
        await asyncio.sleep(1)  # Brief pause between requests


async def interactive_mode():
    """Run in interactive mode for manual testing"""
    print("\n" + "="*80)
    print("Interactive Mode - Strategic Business Travel Assistant")
    print("="*80)
    print("Type your questions below (or 'quit' to exit)\n")
    
    while True:
        try:
            user_input = input("\nYOU: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
                
            if not user_input:
                continue
                
            await send_chat_message(user_input, session_id="interactive")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the Strategic Business Travel Assistant")
    parser.add_argument(
        '--mode',
        choices=['test', 'interactive'],
        default='test',
        help="Run mode: 'test' for automated tests, 'interactive' for manual testing"
    )
    parser.add_argument(
        '--message',
        type=str,
        help="Send a single message (overrides mode)"
    )
    
    args = parser.parse_args()
    
    if args.message:
        # Single message mode
        await send_chat_message(args.message)
    elif args.mode == 'interactive':
        # Interactive mode
        await interactive_mode()
    else:
        # Automated test mode
        await run_tests()


if __name__ == "__main__":
    asyncio.run(main())
