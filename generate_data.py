#!/usr/bin/env python3
"""
Unified data generator for staff and client PII records.
Wraps generate_staff_data.py and generate_client_data.py with a clean CLI.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Import generation functions from existing modules
from generate_staff_data import generate_staff_pii_records
from generate_client_data import generate_client_pii_records

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_staff(args):
    """Generate staff PII records based on CLI arguments."""
    logger.info("Starting staff PII record generation...")
    records = generate_staff_pii_records(
        count=args.count,
        state_bias=args.state,
        state_bias_pct=args.bias
    )

    # Convert records to dictionaries
    records_dict = [record.to_dict() for record in records]

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to JSON file
    with open(args.output, "w") as f:
        json.dump(records_dict, f, indent=2)

    logger.info(f"Successfully generated {len(records)} staff records and written to {args.output}")
    logger.info("Sample record:")
    logger.info(json.dumps(records_dict[0], indent=2))


def generate_client(args):
    """Generate client PII records based on CLI arguments."""
    logger.info("Starting client PII record generation...")
    records = generate_client_pii_records(
        count=args.count,
        state_bias=args.state,
        state_bias_pct=args.bias
    )

    # Convert records to dictionaries
    records_dict = [record.to_dict() for record in records]

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to JSON file
    with open(args.output, "w") as f:
        json.dump(records_dict, f, indent=2)

    logger.info(f"Successfully generated {len(records)} client records and written to {args.output}")
    logger.info("Sample record:")
    logger.info(json.dumps(records_dict[0], indent=2))


def generate_both(args):
    """Generate both staff and client PII records based on CLI arguments."""
    logger.info("Starting generation of both staff and client PII records...")

    # Generate staff records
    logger.info(f"Generating {args.staff_count} staff records...")
    staff_records = generate_staff_pii_records(
        count=args.staff_count,
        state_bias=args.state,
        state_bias_pct=args.bias
    )
    staff_records_dict = [record.to_dict() for record in staff_records]

    # Ensure staff output directory exists
    staff_output_path = Path(args.staff_output)
    staff_output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write staff records to JSON file
    with open(args.staff_output, "w") as f:
        json.dump(staff_records_dict, f, indent=2)
    logger.info(f"Successfully generated {len(staff_records)} staff records and written to {args.staff_output}")

    # Generate client records
    logger.info(f"Generating {args.client_count} client records...")
    client_records = generate_client_pii_records(
        count=args.client_count,
        state_bias=args.state,
        state_bias_pct=args.bias
    )
    client_records_dict = [record.to_dict() for record in client_records]

    # Ensure client output directory exists
    client_output_path = Path(args.client_output)
    client_output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write client records to JSON file
    with open(args.client_output, "w") as f:
        json.dump(client_records_dict, f, indent=2)
    logger.info(f"Successfully generated {len(client_records)} client records and written to {args.client_output}")

    logger.info("\n=== Summary ===")
    logger.info(f"Staff records: {len(staff_records)} -> {args.staff_output}")
    logger.info(f"Client records: {len(client_records)} -> {args.client_output}")


def main():
    """Main entry point with subcommand parsing."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic PII records for testing purposes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 100 staff records with California bias
  %(prog)s staff -c 100 --state "California" --bias 0.3

  # Generate 50 client records to custom path
  %(prog)s client -o outputs/my_clients.json

  # Generate both with different counts
  %(prog)s both --staff-count 100 --client-count 200 --state "Texas"
        """
    )

    subparsers = parser.add_subparsers(
        dest='command',
        help='Type of records to generate',
        required=True
    )

    # Staff subcommand
    staff_parser = subparsers.add_parser(
        'staff',
        help='Generate staff PII records'
    )
    staff_parser.add_argument(
        '-c', '--count',
        type=int,
        default=50,
        help='Number of staff records to generate (default: 50)'
    )
    staff_parser.add_argument(
        '-o', '--output',
        type=str,
        default='outputs/test_staff_records.json',
        help='Output file path for staff records (default: outputs/test_staff_records.json)'
    )
    staff_parser.add_argument(
        '-s', '--state',
        type=str,
        default=None,
        help='State name for geographic bias (e.g., "California", "Texas"). Default: None (uses New Jersey)'
    )
    staff_parser.add_argument(
        '-b', '--bias',
        type=float,
        default=0.1,
        help='State bias percentage 0.0-1.0 (default: 0.1 = 10%% of records use state-specific data)'
    )
    staff_parser.set_defaults(func=generate_staff)

    # Client subcommand
    client_parser = subparsers.add_parser(
        'client',
        help='Generate client PII records'
    )
    client_parser.add_argument(
        '-c', '--count',
        type=int,
        default=50,
        help='Number of client records to generate (default: 50)'
    )
    client_parser.add_argument(
        '-o', '--output',
        type=str,
        default='outputs/client_records.json',
        help='Output file path for client records (default: outputs/client_records.json)'
    )
    client_parser.add_argument(
        '-s', '--state',
        type=str,
        default=None,
        help='State name for geographic bias (e.g., "California", "Texas"). Default: None (uses New Jersey)'
    )
    client_parser.add_argument(
        '-b', '--bias',
        type=float,
        default=0.1,
        help='State bias percentage 0.0-1.0 (default: 0.1 = 10%% of records use state-specific data)'
    )
    client_parser.set_defaults(func=generate_client)

    # Both subcommand
    both_parser = subparsers.add_parser(
        'both',
        help='Generate both staff and client PII records'
    )
    both_parser.add_argument(
        '-sc', '--staff-count',
        type=int,
        default=50,
        help='Number of staff records to generate (default: 50)'
    )
    both_parser.add_argument(
        '-so', '--staff-output',
        type=str,
        default='outputs/test_staff_records.json',
        help='Output file path for staff records (default: outputs/test_staff_records.json)'
    )
    both_parser.add_argument(
        '-cc', '--client-count',
        type=int,
        default=50,
        help='Number of client records to generate (default: 50)'
    )
    both_parser.add_argument(
        '-co', '--client-output',
        type=str,
        default='outputs/client_records.json',
        help='Output file path for client records (default: outputs/client_records.json)'
    )
    both_parser.add_argument(
        '-s', '--state',
        type=str,
        default=None,
        help='State name for geographic bias (e.g., "California", "Texas"). Default: None (uses New Jersey)'
    )
    both_parser.add_argument(
        '-b', '--bias',
        type=float,
        default=0.1,
        help='State bias percentage 0.0-1.0 (default: 0.1 = 10%% of records use state-specific data)'
    )
    both_parser.set_defaults(func=generate_both)

    # Parse arguments and call appropriate function
    args = parser.parse_args()

    # Validate bias percentage
    if hasattr(args, 'bias') and not (0.0 <= args.bias <= 1.0):
        parser.error("Bias percentage must be between 0.0 and 1.0")

    # Call the appropriate handler function
    try:
        args.func(args)
    except Exception as e:
        logger.error(f"Error during generation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
