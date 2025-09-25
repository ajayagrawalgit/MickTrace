"""
Command Line Interface for micktrace.

Provides tools for configuration, monitoring, and log analysis.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config.configuration import configure, get_configuration, Configuration


def configure_command(args: argparse.Namespace) -> None:
    """Configure micktrace from command line."""
    config_args = {}

    if args.level:
        config_args["level"] = args.level

    if args.format:
        config_args["format"] = args.format

    if args.handlers:
        config_args["handlers"] = args.handlers.split(",")

    if args.output:
        # Handle file output
        handlers = []
        for handler in args.output.split(","):
            if handler == "file" and args.file_path:
                handlers.append({
                    "type": "file",
                    "path": args.file_path
                })
            else:
                handlers.append({"type": handler})
        config_args["handlers"] = handlers

    configure(**config_args)
    print("Micktrace configured successfully")


def show_config_command(args: argparse.Namespace) -> None:
    """Show current configuration."""
    config = get_configuration()

    if args.json:
        print(json.dumps(config.to_dict(), indent=2))
    else:
        print(f"Level: {config.level}")
        print(f"Format: {config.format}")
        print(f"Enabled: {config.enabled}")
        print(f"Handlers: {len(config.handlers)}")

        for i, handler in enumerate(config.handlers):
            print(f"  Handler {i+1}: {handler.type} ({handler.level})")


def test_command(args: argparse.Namespace) -> None:
    """Test micktrace configuration."""
    import micktrace

    logger = micktrace.get_logger("micktrace.cli.test")

    print("Testing micktrace configuration...")

    logger.debug("This is a DEBUG message", test=True)
    logger.info("This is an INFO message", test=True) 
    logger.warning("This is a WARNING message", test=True)
    logger.error("This is an ERROR message", test=True)
    logger.critical("This is a CRITICAL message", test=True)

    print("Test completed")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="micktrace",
        description="Micktrace logging library CLI"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Configure command
    config_parser = subparsers.add_parser("configure", help="Configure micktrace")
    config_parser.add_argument("--level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    config_parser.add_argument("--format", choices=["json", "logfmt", "structured", "simple"])
    config_parser.add_argument("--handlers", help="Comma-separated list of handlers")
    config_parser.add_argument("--output", help="Comma-separated list of outputs")
    config_parser.add_argument("--file-path", help="Path for file output")

    # Show config command
    show_parser = subparsers.add_parser("config", help="Show configuration")
    show_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Test command
    test_parser = subparsers.add_parser("test", help="Test configuration")

    # Version command
    version_parser = subparsers.add_parser("version", help="Show version")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "configure":
        configure_command(args)
    elif args.command == "config":
        show_config_command(args)
    elif args.command == "test":
        test_command(args)
    elif args.command == "version":
        print("micktrace 1.0.0")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
