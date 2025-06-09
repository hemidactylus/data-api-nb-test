import json
import os
from typing import Any

from os_lib import locate_summary_filename


class ParsedRun:
    def __init__(self, entries: list[Any]) -> None:
        # Temporary
        self.entries = entries

    def __repr__(self) -> str:
        return f"ParsedRun({self.entries})"


def parse_run_dir(src_dir: str) -> ParsedRun:
    summary_filename = locate_summary_filename(src_dir)
    if summary_filename is None:
        return ParsedRun([])

    return ParsedRun(["filename=" + os.path.join(src_dir, summary_filename)])
