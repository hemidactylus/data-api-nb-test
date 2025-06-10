import os
from datetime import datetime

import matplotlib.pyplot as plt


OBSERVABLES_TO_PRINT = [
    "min",
    "P750",
    "P950",
    "P980",
    "P990",
    "P999",
    "max",
    "mean",
    "median",
]
OBS_STYLE_MAP = {
    "mean": "--",
    "median": ":",
}
OBS_STYLE_DEFAULT = "*-"
FIGURE_FORMAT = (20, 8)


def _plot_obs_map(omap: dict[str, tuple[dict[datetime, float], str]]) -> None:
    for obs in OBSERVABLES_TO_PRINT:
        if obs in omap and omap[obs][0]:
            obs_series, obs_unit0 = omap[obs]
            o_x, o_y0 = list(zip(*(sorted(obs_series.items()))))
            # apply nanoseconds->milliseconds here.
            obs_unit: str
            o_y: list[float]
            if obs_unit0 == "ns":
                obs_unit = "ms"
                o_y = [yval / 1000000.0 for yval in o_y0]
            else:
                obs_unit = obs_unit0
                o_y = o_y0  # type: ignore[assignment]
            obs_style = OBS_STYLE_MAP.get(obs, OBS_STYLE_DEFAULT)
            plt.plot(o_x, o_y, obs_style, label=f"{obs} ({obs_unit})")
    plt.legend()
    plt.xlabel("Run datetime")
    plt.ylabel(obs_unit)


def plot_observables(
    tree: dict[
        str,
        dict[str, dict[str, dict[str, dict[str, tuple[dict[datetime, float], str]]]]],
    ],
    out_dir: str,
) -> list[str]:
    generated_files = []
    print(f"\nPlotting to '{out_dir}' ...")
    # workload->scenario->activity->name->observable->[date->value, unit]
    for _wl, v_wl in tree.items():
        for _sc, v_sc in v_wl.items():
            for _ac, v_ac in v_sc.items():
                for _na, v_na in v_ac.items():
                    # this becomes a single plot with the various curves at once.
                    # select the observables actually to print
                    obs_map = {
                        _ob: v_ob
                        for _ob, v_ob in v_na.items()
                        if _ob in OBSERVABLES_TO_PRINT
                        if v_ob[0]
                    }
                    if obs_map:
                        plot_title = f"{_wl} / {_sc} / {_ac} / {_na}"
                        plot_fileroot = f"{_wl}~{_sc}~{_ac}~{_na}"

                        fig0 = plt.figure(figsize=FIGURE_FORMAT)
                        _plot_obs_map(obs_map)
                        plt.title(plot_title)
                        plt.ylim((0, None))
                        plt.grid()
                        fig_name0 = f"{plot_fileroot}.png"
                        fig_path0 = os.path.join(out_dir, fig_name0)
                        fig0.savefig(fig_path0, bbox_inches="tight")
                        print(f"    * {fig_name0}")
                        generated_files.append(fig_path0)

                        fig1 = plt.figure(figsize=FIGURE_FORMAT)
                        _plot_obs_map(obs_map)
                        plt.title(f"{plot_title} -- Log scale")
                        plt.yscale("log")
                        plt.grid(True, which="both", axis="y")
                        fig_name1 = f"{plot_fileroot}_LOG.png"
                        fig_path1 = os.path.join(out_dir, fig_name1)
                        fig1.savefig(fig_path1, bbox_inches="tight")
                        print(f"    * {fig_name1}")
                        generated_files.append(fig_path1)

    return generated_files
