import os
from datetime import datetime

DATE_FORMAT = "%Y-%m-%d_%H_%M_%S_"
DATE_TAG_LEN = 20


def try_parse_date_tag(dtag) -> datetime | None:
    try:
        return datetime.strptime(dtag, DATE_FORMAT)
    except ValueError:
        return None


def try_parse_dir_name(dir_name: str) -> tuple[datetime, str]:
    dir_date = try_parse_date_tag(dir_name[:DATE_TAG_LEN])
    if dir_date:
        dir_run_name = dir_name[DATE_TAG_LEN:]
        if dir_run_name:
            return (dir_date, dir_run_name)
        else:
            return None
    else:
        return None


def get_input_runs(src_dir: str) -> dict[str, tuple[datetime, str]]:
    ls_full = os.listdir(src_dir)
    return {
        full_dir_name: dir_parsed_pair
        for dir_name in ls_full
        if os.path.isdir(full_dir_name := os.path.join(src_dir, dir_name))
        if (dir_parsed_pair := try_parse_dir_name(dir_name)) is not None
    }


def locate_summary_filename(src_dir: str) -> str | None:
    ls_full = os.listdir(src_dir)
    matching_items = [fn for fn in ls_full if "_summary" in fn]
    if len(matching_items) == 1:
        return matching_items[0]
    elif matching_items == []:
        return None
    else:
        raise Exception(f"Multiple 'summary' candidate files found ({matching_items}).")
