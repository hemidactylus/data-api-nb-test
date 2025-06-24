import os
import re
from typing import Any

from os_lib import locate_metaparameters_filename

LineType = tuple[str, int]

TRACKED_ACTIVITY_NAMES = {"result"}  # , "result_success"}
OBS_NAME_MAP = {
    "count": "count",
    "mean rate": "rate_mean",
    "1-minute rate": "rate_1m",
    "5-minute rate": "rate_5m",
    "15-minute rate": "rate_15m",
    "min": "min",
    "max": "max",
    "mean": "mean",
    "stddev": "stddev",
    "median": "median",
    "75%": "P750",
    "95%": "P950",
    "98%": "P980",
    "99%": "P990",
    "99.9%": "P999",
}
OBS_UNIT_MAP = {
    "calls/nanosecond": "/ns",
    "nanoseconds": "ns",
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
    # TODO parse csv and return it with units (+basic validation)
    return None


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
