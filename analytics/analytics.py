"""
BY WAY OF NOTES

mkdir -p a_inputs
aws s3 cp s3://data-api-nb-test-logs/logs/ a_inputs/ --recursive

mkdir -p a_outputs

===
python analytics.py --input_dir ../_scrap/a_inputs/ --output_dir ../_scrap/a_outputs/
"""

import argparse
from datetime import datetime

from os_lib import get_input_runs
from summary_parsing import parse_run_dir, ParsedRun


def main() -> None:
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
    
    parsed_runs: dict[tuple[datetime, str], ParsedRun] = {
        dir_parsed_pair: parse_run_dir(full_dir_name)
        for full_dir_name, dir_parsed_pair in input_runs.items()
    }

    # sanity checks: I - do workloads from a dir match the workload tagging the dir?
    for (dir_d, wl0), prun in parsed_runs.items():
        for pmset in prun.metric_sets:
            if wl0 != pmset.workload:
                msg = (
                    "Workload mismatch between in-parsed-run and tagged-on-directory. "
                    f"In-run: {pmset}."
                    f"From-dir: {dir_d} / {wl0}."
                )
                raise ValueError(msg)

    # sanity checks: II - are metaparameters constant across runs?
    # TO DO

    # regroup for plottable curves
    # TODO

    print(parsed_runs)

if __name__ == "__main__":
    main()
