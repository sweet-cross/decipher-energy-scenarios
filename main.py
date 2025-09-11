#!/usr/bin/env python3
"""
Swiss Energy Scenarios Decipher System
Main entry point for the multiagent application
"""

import asyncio
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from interfaces.cli_interface import EnergyScenariosCLI

def main():
    """Main entry point."""
    try:
        cli = EnergyScenariosCLI()
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Application error: {str(e)}")
        print("Please check your configuration and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()