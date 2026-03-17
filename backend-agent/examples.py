#!/usr/bin/env python3
"""
Example: Using the Strategic Business Travel Assistant programmatically

This demonstrates how to use the agent directly without the FastAPI wrapper,
which can be useful for integration into other Python applications.
"""

import asyncio
import os
from dotenv import load_dotenv

# Import agent components
from agent import create_travel_agent

# Load environment variables
load_dotenv()


async def example_basic_query():
    """Example 1: Basic weather query"""
    print("\n" + "="*80)
    print("Example 1: Basic Weather Query")
    print("="*80)
    
    agent = create_travel_agent()
    
    result = await agent.ainvoke({
        "input": "What's the weather like in San Francisco?"
    })
    
    print(f"\nAgent Response:\n{result['output']}\n")


async def example_travel_advice():
    """Example 2: Travel advice with flight delay prediction"""
    print("\n" + "="*80)
    print("Example 2: Travel Advice with Flight Delay Prediction")
    print("="*80)
    
    agent = create_travel_agent()
    
    result = await agent.ainvoke({
        "input": "I'm flying to Boston tomorrow for a business meeting. Should I be concerned about weather-related delays?"
    })
    
    print(f"\nAgent Response:\n{result['output']}\n")


async def example_packing_recommendations():
    """Example 3: Detailed packing recommendations"""
    print("\n" + "="*80)
    print("Example 3: Packing Recommendations")
    print("="*80)
    
    agent = create_travel_agent()
    
    result = await agent.ainvoke({
        "input": "I'm going to Stockholm for a week. What should I pack? I'll be doing both indoor meetings and outdoor sightseeing."
    })
    
    print(f"\nAgent Response:\n{result['output']}\n")


async def example_multi_city_comparison():
    """Example 4: Comparing weather in multiple cities"""
    print("\n" + "="*80)
    print("Example 4: Multi-City Comparison")
    print("="*80)
    
    agent = create_travel_agent()
    
    result = await agent.ainvoke({
        "input": "I need to choose between traveling to either London or Paris next week. Which city has better weather?"
    })
    
    print(f"\nAgent Response:\n{result['output']}\n")


async def example_with_intermediate_steps():
    """Example 5: Viewing agent's reasoning process"""
    print("\n" + "="*80)
    print("Example 5: Agent Reasoning Process")
    print("="*80)
    
    agent = create_travel_agent()
    
    result = await agent.ainvoke({
        "input": "What's the weather forecast for Dubai? I'm concerned about the heat."
    })
    
    print("\n--- Agent's Thought Process ---")
    if "intermediate_steps" in result:
        for i, (action, observation) in enumerate(result["intermediate_steps"], 1):
            print(f"\nStep {i}:")
            print(f"Action: {action.tool}")
            print(f"Input: {action.tool_input}")
            print(f"Observation: {str(observation)[:200]}...")  # Truncate long outputs
    
    print(f"\n--- Final Response ---\n{result['output']}\n")


async def example_custom_context():
    """Example 6: Using custom context or constraints"""
    print("\n" + "="*80)
    print("Example 6: Travel Advice with Specific Constraints")
    print("="*80)
    
    agent = create_travel_agent()
    
    result = await agent.ainvoke({
        "input": """I'm traveling to Singapore next Tuesday with my 5-year-old daughter. 
        We'll be visiting outdoor attractions like Gardens by the Bay. 
        What should I know about the weather and what should we bring?"""
    })
    
    print(f"\nAgent Response:\n{result['output']}\n")


async def example_error_handling():
    """Example 7: Handling invalid city names"""
    print("\n" + "="*80)
    print("Example 7: Error Handling - Invalid City")
    print("="*80)
    
    agent = create_travel_agent()
    
    result = await agent.ainvoke({
        "input": "What's the weather in XYZ123?" # Invalid city name
    })
    
    print(f"\nAgent Response:\n{result['output']}\n")
    print("Note: The agent gracefully handles errors and provides helpful feedback.")


async def run_all_examples():
    """Run all examples sequentially"""
    print("\n" + "="*80)
    print("Strategic Business Travel Assistant - Programmatic Examples")
    print("="*80)
    print("\nThese examples demonstrate various use cases for the travel assistant agent.")
    
    examples = [
        example_basic_query,
        example_travel_advice,
        example_packing_recommendations,
        example_multi_city_comparison,
        example_with_intermediate_steps,
        example_custom_context,
        example_error_handling,
    ]
    
    for example in examples:
        try:
            await example()
            await asyncio.sleep(1)  # Brief pause between examples
        except Exception as e:
            print(f"\n❌ Error in {example.__name__}: {str(e)}\n")
    
    print("\n" + "="*80)
    print("All examples completed!")
    print("="*80 + "\n")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run examples of the Strategic Business Travel Assistant"
    )
    parser.add_argument(
        '--example',
        type=int,
        choices=range(1, 8),
        help="Run a specific example (1-7)"
    )
    
    args = parser.parse_args()
    
    examples = {
        1: example_basic_query,
        2: example_travel_advice,
        3: example_packing_recommendations,
        4: example_multi_city_comparison,
        5: example_with_intermediate_steps,
        6: example_custom_context,
        7: example_error_handling,
    }
    
    if args.example:
        # Run specific example
        await examples[args.example]()
    else:
        # Run all examples
        await run_all_examples()


if __name__ == "__main__":
    # Check if required environment variables are set
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ ERROR: OPENAI_API_KEY not found in environment variables.")
        print("Please set it in your .env file or export it:")
        print("  export OPENAI_API_KEY='your-key-here'\n")
        exit(1)
    
    if not os.getenv("OPENWEATHER_API_KEY"):
        print("\n❌ ERROR: OPENWEATHER_API_KEY not found in environment variables.")
        print("Please set it in your .env file or export it:")
        print("  export OPENWEATHER_API_KEY='your-key-here'\n")
        exit(1)
    
    # Run examples
    asyncio.run(main())
