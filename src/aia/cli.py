
import argparse
import sys
import os
from .exporter import HoldingsExporter
from .utils import log

def main():
    parser = argparse.ArgumentParser(description="AIA CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: export-holdings
    parser_export = subparsers.add_parser("export-holdings", help="Export current holdings to JSON")
    parser_export.add_argument("--output", "-o", help="Output file path", default="output/holdings_snapshot.json")

    args = parser.parse_args()

    if args.command == "export-holdings":
        exporter = HoldingsExporter()
        
        # Determine absolute path for output default
        output_path = args.output
        if not os.path.isabs(output_path):
            # Default to project root / output if relative
            # Assuming we run from project root, or we can use __file__ to find root
            # Let's rely on CWD for consistent behavior with spec "AIA_PROJECT_ROOT/output"
            output_path = os.path.abspath(output_path)

        log(f"Exporting holdings to {output_path}...")
        success = exporter.export(output_path)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
