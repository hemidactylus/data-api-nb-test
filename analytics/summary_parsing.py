import json
import os
from typing import Any

from os_lib import locate_summary_filename, locate_metaparameters_filename


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


def load_activity_desc(ad_line: str) -> dict[str, Any]:
    assert ad_line[0] == "{"
    assert ad_line[-1] == "}"
    body = ad_line[1:-1]
    pairs_s = [
        pair_s.split("=")
        for pair_s in body.split(",")
    ]
    assert all(len(pair_s) == 2 for pair_s in pairs_s)
    return dict([pair_s[0], json.loads(pair_s[1])] for pair_s in pairs_s)


def is_useful_activity(a_desc: dict[str, Any]) -> bool:
    if "activity" not in a_desc:
        # this is a gauge or other non-interesting metric item
        return False
    if a_desc["activity"] in {"schema", "rampup"}:
        return False
    if a_desc["name"] not in TRACKED_ACTIVITY_NAMES:
        return False
    return True


def is_separator_line(line: str) -> bool:
    if "====" in line:
        return True
    if "----" in line:
        return True
    return False


def parse_lines_to_metric_map(lines: list[str]) -> dict[str, tuple[float, str]]:
    def _parse_line(_line: str) -> tuple[str, tuple[float, str]] | None:
        line = _line.replace("<=", "=")
        if " = " not in line:
            return None

        raw_obs, raw_val_s = [part.strip() for part in line.split(" = ")]
        obs_name = OBS_NAME_MAP[raw_obs]
        val_parts = [part.strip() for part in raw_val_s.split(" ") if part.strip()]

        obs_val: tuple[float, str]
        if len(val_parts) == 1:
            obs_val = (float(val_parts[0]), "")
        elif len(val_parts) == 2:
            obs_val = (float(val_parts[0]), OBS_UNIT_MAP[val_parts[1]])
        else:
            raise ValueError(f"Unexpected observable format from line {_line}")

        return (obs_name, obs_val)

    return dict(_parsed for ln in lines if (_parsed := _parse_line(ln)) is not None)


def load_metric_sets(s_filepath: str) -> list[ParsedMetricSet]:
    this_ms_json: dict[str, Any] | None = None
    these_lines: list[str] = []
    found_metric_lines: list[ParsedMetricSet] = []

    def _flush_buffer() -> None:
        nonlocal these_lines, this_ms_json, found_metric_lines
        if these_lines and this_ms_json is not None:
            # parse lines quoting a measurement
            parsed_metric_map = parse_lines_to_metric_map(these_lines)
            if parsed_metric_map:
                found_metric_lines.append(
                    ParsedMetricSet(
                        workload=this_ms_json["workload"],
                        scenario=this_ms_json["scenario"],
                        activity=this_ms_json["activity"],
                        name=this_ms_json["name"],
                        metrics=parsed_metric_map,
                    )
                )
        these_lines = []
        this_ms_json = None

    for _line in open(s_filepath).readlines():
        line = _line.strip()
        if line:
            if line[0] == "{":
                # the lone defines an activity
                a_desc = load_activity_desc(line)
                _flush_buffer()
                if is_useful_activity(a_desc):
                    this_ms_json = a_desc
            elif is_separator_line(line):
                _flush_buffer()
            else:
                if this_ms_json is not None:
                    these_lines.append(line)
    _flush_buffer()
    return found_metric_lines


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
    summary_filename = locate_summary_filename(src_dir)
    metaparameters_filename = locate_metaparameters_filename(src_dir)

    metaparameters: dict[str, str]
    if metaparameters_filename:
        metaparameters = load_metaparameters(
            os.path.join(src_dir, metaparameters_filename),
        )
    else:
        metaparameters = {}

    metric_sets: list[ParsedMetricSet]
    if summary_filename:
        metric_sets = load_metric_sets(
            os.path.join(src_dir, summary_filename),
        )
    else:
        metric_sets = []

    return ParsedRun(metric_sets=metric_sets, metaparameters=metaparameters)
