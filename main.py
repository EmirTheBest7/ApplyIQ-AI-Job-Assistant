"""
Main entry point for the ApplyIQ Application Assistant.
"""

import sys
import logging

if __name__ == '__main__':
    try:
        from cli import cli
        cli()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        logging.exception("Unhandled exception")
        sys.exit(1)
