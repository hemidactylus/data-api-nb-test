import os
import re
from typing import Any

from os_lib import locate_metaparameters_filename

LineType = tuple[str, int]

TRACKED_ACTIVITY_NAMES = {"result", "result_success"}
UNIT_LABELS = {"duration_unit", "rate_unit"}
OBS_TO_UNIT_TYPE = {
    "count": "",
    "min": "duration_unit",
    "max": "duration_unit",
    "mean": "duration_unit",
    "stddev": "duration_unit",
    "p50": "duration_unit",
    "p75": "duration_unit",
    "p95": "duration_unit",
    "p98": "duration_unit",
    "p99": "duration_unit",
    "p999": "duration_unit",
    "mean_rate": "rate_unit",
    "m1_rate": "rate_unit",
    "m5_rate": "rate_unit",
    "m15_rate": "rate_unit",
}
OBS_NAME_MAP = {
    "count": "count",
    #
    "min": "min",
    "max": "max",
    "mean": "mean",
    "stddev": "stddev",
    "p50": "P500",
    "p75": "P750",
    "p95": "P950",
    "p98": "P980",
    "p99": "P990",
    "p999": "P999",
    #
    "mean_rate": "rate_mean",
    "m1_rate": "rate_1m",
    "m5_rate": "rate_5m",
    "m15_rate": "rate_15m",
}
OBS_UNIT_MAP = {
    "calls/SECONDS": "/s",
    "NANOSECONDS": "ns",
    "": "",
}

CSV_FILE_PATTERN = re.compile(
    r'^(?P<scenario>.*?)__' +
    r'(?P<activity>.*?)__' +
    r'(?P<name>.*?)_container_(?P<container>.*?)___workload_(?P<workload>.*?)\.csv$'
)

class ParsedMetricSet:
    workload: str
    scenario: str
    activity: str
    name: str
    metrics: dict[str, tuple[float, str]]

    def __init__(
        self,
        *,
        workload: str,
        scenario: str,
        activity: str,
        name: str,
        metrics: dict[str, tuple[float, str]],
    ) -> None:
        self.workload = workload
        self.scenario = scenario
        self.activity = activity
        self.name = name
        self.metrics = metrics

    def __repr__(self) -> str:
        _desc = f"{self.workload}/{self.scenario}/{self.activity}/{self.name}"
        if "mean" in self.metrics:
            return f"{_desc}(mean={self.metrics['mean'][0]})"
        else:
            return f"{_desc}()"


class ParsedRun:
    metric_sets: list[ParsedMetricSet]
    metaparameters: dict[str, str] | None

    def __init__(
        self,
        *,
        metric_sets: list[ParsedMetricSet],
        metaparameters: dict[str, str] | None,
    ) -> None:
        # Temporary
        self.metric_sets = metric_sets
        self.metaparameters = metaparameters

    def __repr__(self) -> str:
        return f"ParsedRun({self.metric_sets}; meta={self.metaparameters})"


def load_metaparameters(mp_filepath: str) -> dict[str, str]:
    return dict(
        list(pc.strip() for pc in fl.split("="))
        for fl in open(mp_filepath).readlines()
        if fl.strip() != ""
        if fl.strip()[0] != "#"
    )


def csv_filename_to_activity_desc(fname: str) -> dict[str, Any] | None:
    match = CSV_FILE_PATTERN.match(fname)
    if match:
        return match.groupdict()
    else:
        return None


def is_useful_activity(a_desc: dict[str, Any]) -> bool:
    if "activity" not in a_desc:
        # this is a gauge or other non-interesting metric item
        return False
    if a_desc["activity"] in {"schema", "rampup"}:
        return False
    if a_desc["name"] not in TRACKED_ACTIVITY_NAMES:
        return False
    return True


def load_csv_metrics(fpath: str) -> dict[str, tuple[float, str]] | None:
    """
    Read a CSV with metrics, pick relevant columns, return map
        name -> (value, unit)
    also dealing with filtering/average of rows. Return None if unsuitable data.
    """
    with open(fpath) as ofile:
        lines = list(ofile.readlines())
        if not lines:
            print(
                f"** No lines found in file {fpath}."
                f"File will not be loaded."
            )
            return None
        header, rows = lines[0], [_line.strip() for _line in lines[1:] if _line.strip()]
        if not rows:
            print(
                f"** No data lines found in file {fpath}."
                f"File will not be loaded."
            )
            return None
        column_labels = [lab.strip() for lab in header.split(",")]
        value_columns: dict[str, list[str]] = {lab: [] for lab in column_labels}
        for _line_no, row in enumerate(rows):
            line_no = _line_no + 2
            val_strings = [val_str.strip() for val_str in row.split(",")]
            if len(val_strings) != len(column_labels):
                print(
                    f"** Row/label mismatch in file {fpath} at line "
                    f"{line_no}. File will not be loaded."
                )
                return None
            for col_lab, val_str in zip(column_labels, val_strings):
                value_columns[col_lab] += [val_str]
        # post-processing
        unit_map = {
            c_label: c_vals
            for c_label, c_vals in value_columns.items()
            if c_label in UNIT_LABELS
        }
        if any(len(set(um_val)) > 1 for um_val in unit_map.values()):
            print(
                f"** Inhomogeneous unit labels found in file {fpath}: "
                f"{unit_map}. File will not be loaded."
            )
            return None
        obs_lists = {
            c_label: [float(c_val) for c_val in c_vals]
            for c_label, c_vals in value_columns.items()
            if c_label in OBS_NAME_MAP
        }
        # TODO: improve this logic!
        rows_to_keep = [row_i for row_i, row in enumerate(obs_lists["count"])]
        if not rows_to_keep:
            print(
                f"** No admissible data lines found in file {fpath}."
                f"File will not be loaded."
            )
            return None

        # averages are weighted on 'counts'
        counts = [obs_lists["count"][row_i] for row_i in rows_to_keep]
        total_counts = sum(counts)

        def _average(val_list):
            return sum(val_list[row_i] * cnt for row_i, cnt in zip(rows_to_keep, counts)) / total_counts

        averages = {
            c_label: _average(c_obslist)
            for c_label, c_obslist in obs_lists.items()
        }
        # overwrite 'count' average
        final_values = {
            **averages,
            **{"count": total_counts},
        }
        # unit management
        obs_name_to_unit = {
            **{
                c_unn: OBS_UNIT_MAP[c_uns[0]]
                for c_unn, c_uns in unit_map.items()
            },
            **{"": ""},
        }
        values_with_unit = {
            OBS_NAME_MAP[c_label]: (c_value, obs_name_to_unit[OBS_TO_UNIT_TYPE[c_label]])
            for c_label, c_value in final_values.items()
        }
        return values_with_unit


def load_metric_csvs(src_dir: str) -> list[ParsedMetricSet]:
    """
    Scans files in a directory, pick those expressing metrics of interest, and
    return their contents as a ParsedMetricSet (in part. averaged over csv rows).
    """
    print(f"Loading CSVs from {src_dir}")

    all_csvs = [
        (fpath, fname)
        for fname in os.listdir(src_dir)
        if fname[-4:].lower() == ".csv"
        if os.path.isfile(fpath := os.path.join(src_dir, fname))
    ]
    csv_to_activity_desc = {
        fpath: activity_desc
        for fpath, fname in all_csvs
        if (activity_desc := csv_filename_to_activity_desc(fname)) is not None
        if is_useful_activity(activity_desc)
    }
    print(f"    Found {len(csv_to_activity_desc)} suitable metric csv.")


    parsed_metric_sets: list[ParsedMetricSet] = []
    for fpath, activity_desc in csv_to_activity_desc.items():
        print(f"    * '{fpath}' ... ", end="")
        metrics = load_csv_metrics(fpath)
        if metrics:
            print("OK")
            parsed_metric_sets.append(
                ParsedMetricSet(
                    workload=activity_desc["workload"],
                    scenario=activity_desc["scenario"],
                    activity=activity_desc["activity"],
                    name=activity_desc["name"],
                    metrics=metrics,
                )
            )
        else:
            print("Invalid/missing data found.")
    return parsed_metric_sets


def parse_run_dir(src_dir: str) -> ParsedRun:
    """
    Parse a whole run directory into a cleaned data structure
    isomorphic to the directory contents.

    The return type of this function has the shape (schematically):

        * metaparameters (map)
        * metric_sets (list): [
            (workload,scenario,activity,name, {obs: (val, unit), ...},
            ...
        ]
    """
    print(f"Parsing {src_dir}")

    metaparameters_filename = locate_metaparameters_filename(src_dir)

    metaparameters: dict[str, str]
    if metaparameters_filename:
        print(f"  Loading {metaparameters_filename}")
        metaparameters = load_metaparameters(
            os.path.join(src_dir, metaparameters_filename),
        )
    else:
        metaparameters = {}

    metric_sets = load_metric_csvs(src_dir)

    print(f"Done parsing {src_dir}\n")
    return ParsedRun(metric_sets=metric_sets, metaparameters=metaparameters)
