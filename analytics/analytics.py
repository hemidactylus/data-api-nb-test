"""
BY WAY OF NOTES

mkdir -p a_inputs
aws s3 cp s3://data-api-nb-test-logs/logs/ a_inputs/ --recursive

mkdir -p a_outputs

===
python analytics.py --input_dir ../_scrap/a_inputs/ --output_dir ../_scrap/a_outputs/
"""

import argparse

from os_lib import get_input_runs
from summary_parsing import parse_run_dir, ParsedRun


def main():
    parser = argparse.ArgumentParser(description="Analysis of Data API nb perf tests.")
    parser.add_argument(
        "--input_dir",
        type=str,
        default="logs",
        help="Path to the input directory (default: 'logs')"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="output",
        help="Path to the output directory (default: 'output')"
    )
    
    args = parser.parse_args()

    print(f"Output directory: {args.output_dir}")

    input_runs: dict[str, tuple[datetime, str]] = get_input_runs(args.input_dir)
    
    parsed_runs: dict[tuple[datetime, str], list[ParsedRun]] = {
        dir_parsed_pair: parse_run_dir(full_dir_name)
        for full_dir_name, dir_parsed_pair in input_runs.items()
    }
    print(parsed_runs)

if __name__ == "__main__":
    main()
