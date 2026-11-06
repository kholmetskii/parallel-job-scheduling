"""Plot saved randomized-policy results across server counts."""

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator, ScalarFormatter


def main() -> None:
    project = Path(__file__).resolve().parent
    source = project / "results" / "randomized_servers.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    summaries = sorted(data["summaries"], key=lambda row: row["servers"])
    counts = [row["servers"] for row in summaries]
    settings = data["measurement"]
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 11,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#BDC7D3", "axes.labelcolor": "#243447",
        "xtick.color": "#475569", "ytick.color": "#475569",
        "svg.fonttype": "none", "svg.hashsalt": "parallel-job-scheduling-server-counts",
    })
    figure, axes = plt.subplots(1, 2, figsize=(12.8, 7.4))
    figure.subplots_adjust(left=0.08, right=0.97, bottom=0.28, top=0.73, wspace=0.27)
    figure.text(0.06, 0.965, "Randomized allocation as the system grows", fontsize=22,
                weight="bold", color="#18334C", va="top")
    figure.text(0.06, 0.90,
                "Arrival rate = 0.8 × servers · mean job size = 1 · same policy probabilities",
                fontsize=11, color="#526579", va="top")
    figure.text(0.06, 0.848,
                f"{len(data['workload_seeds'])} seeds per size · "
                f"{settings['warmup_arrivals']:,} warm-up + "
                f"{settings['measured_arrivals']:,} measured arrivals per run",
                fontsize=11, color="#526579", va="top")
    for axis, metric, scale, title, ylabel in (
        (axes[0], "blocking_probability", 100, "Blocking probability", "Rejected arrivals (%)"),
        (axes[1], "mean_execution_time", 1, "Accepted-job execution time", "Time units"),
    ):
        means = [row[f"{metric}_mean"] * scale for row in summaries]
        deviations = [row[f"{metric}_sd"] * scale for row in summaries]
        for row in data["runs"]:
            axis.scatter(row["servers"], row[metric] * scale, s=22,
                         color="#8FAEC3", alpha=0.65, zorder=2)
        axis.errorbar(counts, means, yerr=deviations, fmt="D-", color="#245F86",
                      markersize=5, linewidth=1.6, capsize=5, zorder=4)
        axis.set_xscale("log")
        axis.set_xticks(counts)
        axis.xaxis.set_major_formatter(ScalarFormatter())
        axis.minorticks_off()
        axis.set_xlim(counts[0] / 1.2, counts[-1] * 1.2)
        upper = max(average + sd for average, sd in zip(means, deviations))
        axis.set_ylim(0, upper * 1.20)
        axis.yaxis.set_major_locator(MaxNLocator(nbins=6))
        axis.set_xlabel("Number of servers (log scale)", labelpad=9)
        axis.set_ylabel(ylabel, labelpad=9)
        axis.set_title(title, fontsize=13, weight="bold", color="#243447", pad=15)
        axis.grid(axis="y", color="#E3EAF0", linewidth=0.8)
        axis.set_axisbelow(True)
        for index in (0, len(counts) - 1):
            label = f"{means[index]:.2f}%" if scale == 100 else f"{means[index]:.4f}"
            axis.annotate(label, (counts[index], means[index] + deviations[index]),
                          xytext=(0, 9), textcoords="offset points", ha="center",
                          color="#18334C", weight="bold", fontsize=10)
    benchmark = data["large_system_execution_benchmark"]
    axes[1].axhline(benchmark, color="#687988", linestyle="--", linewidth=1.3)
    handles = [Line2D([0], [0], marker="o", linestyle="none", color="#8FAEC3",
                      markersize=5, label="One seed"),
               Line2D([0], [0], marker="D", color="#245F86", markersize=5,
                      label="Mean ±1 SD"),
               Line2D([0], [0], color="#687988", linestyle="--",
                      label=f"Large-system benchmark ({benchmark:.3f})")]
    figure.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.53, 0.16),
                  ncol=3, frameon=False, fontsize=10, columnspacing=2)
    figure.text(0.06, 0.125,
                "Bars show one sample standard deviation across seeds, not confidence intervals. Lines connect means.\n"
                "Execution time includes accepted jobs only. The benchmark describes the large-system limit.\n"
                "Load per server stays constant; larger systems receive more arrivals per time unit.",
                fontsize=9.5, color="#526579", va="top", linespacing=1.5)
    output = project / "results" / "figures"
    output.mkdir(parents=True, exist_ok=True)
    description = ("Randomized allocation at fixed offered load per server. Mean and one sample SD. "
                   f"Source: results/randomized_servers.json; SHA256: {hashlib.sha256(source.read_bytes()).hexdigest()}")
    for extension in ("png", "svg"):
        metadata = {"Title": "Randomized allocation across server counts", "Description": description}
        if extension == "svg":
            metadata["Date"] = None
        figure.savefig(output / f"randomized_servers.{extension}", dpi=300,
                       facecolor="white", metadata=metadata)
        print(f"Saved results/figures/randomized_servers.{extension}")
    plt.close(figure)


if __name__ == "__main__":
    main()
