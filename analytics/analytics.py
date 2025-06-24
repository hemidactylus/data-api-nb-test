"""
BY WAY OF NOTES

mkdir -p a_inputs
aws s3 cp s3://data-api-nb-test-logs/logs/ a_inputs/ --recursive

mkdir -p a_outputs

===
python analytics.py --input_dir ../_scrap/a_inputs/ --output_dir ../_scrap/a_outputs/
"""

import argparse
import json
import os
from datetime import datetime

from atlassian_lib import update_atlassian_page
from obs_plotting import plot_observables
from os_lib import get_input_runs
from summary_parsing import parse_run_dir, ParsedRun


PLOTTABLE_JSON_FILETITLE = "full_plottable_output.json"
DATETIME_FORMAT = "%Y-%m-%d_%H_%M_%S"


def date_to_string(dt: datetime) -> str:
    return dt.strftime(DATETIME_FORMAT)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analysis of Data API nb perf tests.")
    parser.add_argument(
        "--input_dir",
        type=str,
        default="logs",
        help=(
            "Path to the input directory (default: 'logs'). "
            "Subdirs are one per run and workload"
        ),
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="output",
        help="Path to the output directory (default: 'output')",
    )
    parser.add_argument(
        "--atlassian",
        action="store_true",
        help="Upload a summary page on Atlassian (requires access setup)",
    )

    args = parser.parse_args()

    plottable_json_filename = os.path.join(args.output_dir, PLOTTABLE_JSON_FILETITLE)

    print(f"Input directory: {args.input_dir}")
    print(f"Output plottable JSON: {plottable_json_filename}")

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
    # TODO

    # sanity checks: III - are units consistent for a given observable?
    # TODO

    # regroup for plottable curves. This is a map:
    #   workload->scenario->activity->name->observable->[date->value, unit]
    plottable_tree: dict[
        str,
        dict[str, dict[str, dict[str, dict[str, tuple[dict[datetime, float], str]]]]],
    ] = {}
    for (_date, _), _prun in parsed_runs.items():
        for _mset in _prun.metric_sets:
            _workload = _mset.workload
            _scenario = _mset.scenario
            _activity = _mset.activity
            _name = _mset.name
            for _observable, (_value, _unit) in _mset.metrics.items():
                # add room to the tree if necessary
                if _workload not in plottable_tree:
                    plottable_tree[_workload] = {}
                if _scenario not in plottable_tree[_workload]:
                    plottable_tree[_workload][_scenario] = {}
                if _activity not in plottable_tree[_workload][_scenario]:
                    plottable_tree[_workload][_scenario][_activity] = {}
                if _name not in plottable_tree[_workload][_scenario][_activity]:
                    plottable_tree[_workload][_scenario][_activity][_name] = {}
                if _name not in plottable_tree[_workload][_scenario][_activity]:
                    plottable_tree[_workload][_scenario][_activity][_name] = {}
                if (
                    _observable
                    not in plottable_tree[_workload][_scenario][_activity][_name]
                ):
                    plottable_tree[_workload][_scenario][_activity][_name][
                        _observable
                    ] = ({}, _unit)
                # add data point
                plottable_tree[_workload][_scenario][_activity][_name][_observable][0][
                    _date
                ] = _value
    # dump as JSON (requires taming datetime keys into strings)
    dumpable_tree = {
        _wl: {
            _sc: {
                _ac: {
                    _na: {
                        _ob: (
                            {date_to_string(_da): _va for _da, _va in v_ob.items()},
                            _un,
                        )
                        for _ob, (v_ob, _un) in v_na.items()
                    }
                    for _na, v_na in v_ac.items()
                }
                for _ac, v_ac in v_sc.items()
            }
            for _sc, v_sc in v_wl.items()
        }
        for _wl, v_wl in plottable_tree.items()
    }
    with open(plottable_json_filename, "w") as o_file:
        json.dump(dumpable_tree, o_file, indent=2, sort_keys=True)

    generated_plot_map = plot_observables(plottable_tree, args.output_dir)
    num_generated_plots = len(
        [
            plt_pair
            for wlmap in generated_plot_map.values()
            for scmap in wlmap.values()
            for acmap in scmap.values()
            for nalist in acmap.values()
            for plt_pair in nalist
        ]
    )
    print(f"Generated {num_generated_plots} plots.")

    # prepare and upload the Atlassian page
    if args.atlassian:
        update_atlassian_page(
            parsed_runs,
            plottable_tree,
            generated_plot_map,
        )
        print("Page updated to Atlassian.")


if __name__ == "__main__":
    main()

    print("Finished.")
