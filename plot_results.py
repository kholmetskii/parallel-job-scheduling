"""Create PNG and SVG figures from the saved M6 experiment, without rerunning it."""

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter, MaxNLocator


def main() -> None:
    project = Path(__file__).resolve().parent
    source = project / "results" / "greedy_experiment.json"
    experiment = json.loads(source.read_text(encoding="utf-8"))
    summaries = experiment["summaries"]
    base_warmup = experiment["baseline"]["warmup_arrivals"]
    base_measured = experiment["baseline"]["measured_arrivals"]
    baseline = next(row for row in summaries
                    if (row["warmup_arrivals"], row["measured_arrivals"])
                    == (base_warmup, base_measured))
    warmups = sorted((row for row in summaries if row["measured_arrivals"] == base_measured),
                     key=lambda row: row["warmup_arrivals"])
    lengths = sorted((row for row in summaries if row["warmup_arrivals"] == base_warmup),
                     key=lambda row: row["measured_arrivals"])
    if any(row["runs"] != baseline["runs"] for row in warmups + lengths):
        raise ValueError("All plotted configurations must have the same number of seeds")

    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 11,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#BDC7D3", "axes.labelcolor": "#243447",
        "xtick.color": "#475569", "ytick.color": "#475569",
        "svg.fonttype": "none", "svg.hashsalt": "parallel-job-scheduling-m6",
    })
    figure, axes = plt.subplots(2, 2, figsize=(12.8, 9.8))
    figure.subplots_adjust(left=0.09, right=0.975, bottom=0.20, top=0.71,
                           hspace=0.75, wspace=0.28)
    figure.text(0.06, 0.965, "Greedy allocation: 100-server experiment",
                fontsize=22, weight="bold", color="#18334C", va="top")
    figure.text(0.06, 0.922,
                f"{len(experiment['runs'])} runs · {baseline['runs']} seeds per configuration · "
                "Poisson arrival rate 80 · mean job size 1",
                fontsize=11, color="#526579", va="top")
    figure.text(0.06, 0.865,
                f"Selected baseline: {base_warmup:,} warm-up + {base_measured:,} measured arrivals\n"
                f"Blocking: {baseline['blocking_probability_mean']:.3%}     "
                f"Mean execution: {baseline['mean_execution_time_mean']:.6f} time units",
                fontsize=12, color="#7D3B16", va="top", linespacing=1.6,
                bbox={"boxstyle": "round,pad=0.65", "facecolor": "#FFF3E8", "edgecolor": "none"})

    metrics = (("blocking_probability", 100.0, "Blocking probability (%)", "%.1f"),
               ("mean_execution_time", 1.0, "Mean execution time\n(time units)", "%.3f"))
    comparisons = ((warmups, "warmup_arrivals", "Warm-up arrivals",
                    f"Warm-up length\n{base_measured:,} measured arrivals"),
                   (lengths, "measured_arrivals", "Measured arrivals",
                    f"Measured run length\n{base_warmup:,} warm-up arrivals"))
    legend_handles = {}
    for row_index, (metric, scale, ylabel, number_format) in enumerate(metrics):
        all_rows = warmups + lengths
        lower = min((row[f"{metric}_mean"] - row[f"{metric}_sd"]) * scale for row in all_rows)
        upper = max((row[f"{metric}_mean"] + row[f"{metric}_sd"]) * scale for row in all_rows)
        padding = max((upper - lower) * 0.18, 1e-6)
        for column, (rows, x_field, xlabel, title) in enumerate(comparisons):
            axis = axes[row_index, column]
            for index, row in enumerate(rows):
                selected = (row["warmup_arrivals"], row["measured_arrivals"]) == (base_warmup, base_measured)
                color = "#C45E24" if selected else "#2F6F98"
                handle = axis.errorbar(
                    index, row[f"{metric}_mean"] * scale,
                    yerr=row[f"{metric}_sd"] * scale,
                    fmt="D" if selected else "o", color=color,
                    markersize=7, capsize=5, capthick=1.5, elinewidth=1.7,
                )
                label = "Selected baseline" if selected else "Other configurations"
                legend_handles.setdefault(label, handle)
            axis.set_xticks(range(len(rows)), [f"{row[x_field]:,}" for row in rows])
            axis.set_xlim(-0.45, len(rows) - 0.55)
            axis.set_ylim(lower - padding, upper + padding)
            axis.yaxis.set_major_locator(MaxNLocator(nbins=5, steps=[1, 2, 5, 10]))
            axis.yaxis.set_major_formatter(FormatStrFormatter(number_format))
            axis.set_xlabel(xlabel, labelpad=9)
            axis.set_ylabel(ylabel, labelpad=9)
            axis.set_title(title, fontsize=12, weight="bold", color="#243447", pad=13)
            axis.grid(axis="y", color="#E3EAF0", linewidth=0.8)
            axis.set_axisbelow(True)

    figure.legend(list(legend_handles.values()), list(legend_handles),
                  loc="lower center", bbox_to_anchor=(0.53, 0.105),
                  ncol=2, frameon=False, columnspacing=3)
    figure.text(0.06, 0.073,
                f"Points = mean of {baseline['runs']} seeds; bars = ±1 sample standard deviation across seeds.\n"
                "Bars describe run-to-run variability; they are not confidence intervals.\n"
                "Vertical axes show restricted ranges to make small differences visible.",
                fontsize=10, color="#526579", va="top", linespacing=1.6)
    output = project / "results" / "figures"
    output.mkdir(parents=True, exist_ok=True)
    description = ("M6 sensitivity results. Points are means; error bars are one sample SD across seeds. "
                   f"Source: results/greedy_experiment.json; SHA256: {hashlib.sha256(source.read_bytes()).hexdigest()}")
    for extension in ("png", "svg"):
        path = output / f"greedy_sensitivity.{extension}"
        metadata = {"Title": "Greedy allocation: 100-server experiment", "Description": description}
        if extension == "svg":
            metadata["Date"] = None
        figure.savefig(path, dpi=300, facecolor="white", metadata=metadata)
        print(f"Saved results/figures/{path.name}")
    plt.close(figure)


if __name__ == "__main__":
    main()
