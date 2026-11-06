"""Plot the saved M7 policy comparison as paired seed results and means."""

import hashlib
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FormatStrFormatter, MaxNLocator


def main() -> None:
    project = Path(__file__).resolve().parent
    source = project / "results" / "policy_comparison.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    key = (data["baseline"]["warmup_arrivals"], data["baseline"]["measured_arrivals"])
    rows = [row for row in data["runs"]
            if (row["warmup_arrivals"], row["measured_arrivals"]) == key]
    summaries = {row["policy"]: row for row in data["summaries"]
                 if (row["warmup_arrivals"], row["measured_arrivals"]) == key}
    by_policy = {name: {row["seed"]: row for row in rows if row["policy"] == name}
                 for name in ("greedy", "randomized")}
    seeds = sorted(by_policy["greedy"])
    if len(seeds) < 2 or set(seeds) != by_policy["randomized"].keys():
        raise ValueError("The figure requires matched workload seeds")
    for seed in seeds:
        if by_policy["greedy"][seed]["workload_sha256"] != by_policy["randomized"][seed]["workload_sha256"]:
            raise ValueError("The policies did not receive identical workloads")
    greedy, randomized = summaries["greedy"], summaries["randomized"]
    colors = ("#2F6F98", "#C45E24")
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 11,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#BDC7D3", "axes.labelcolor": "#243447",
        "xtick.color": "#475569", "ytick.color": "#475569",
        "svg.fonttype": "none", "svg.hashsalt": "parallel-job-scheduling-m7",
    })
    figure, axes = plt.subplots(1, 2, figsize=(12.8, 8.0))
    figure.subplots_adjust(left=0.09, right=0.97, bottom=0.23, top=0.65, wspace=0.30)
    figure.text(0.06, 0.965, "Greedy vs randomized allocation", fontsize=23,
                weight="bold", color="#18334C", va="top")
    figure.text(0.06, 0.913,
                f"100 servers · arrival rate 80 · {len(seeds)} paired workloads · "
                f"{key[0]:,} warm-up + {key[1]:,} measured arrivals",
                fontsize=11, color="#526579", va="top")
    delta = data["paired_policy_differences"]["summary"]
    figure.text(0.06, 0.847,
                f"Blocking: {greedy['blocking_probability_mean']:.3%} → "
                f"{randomized['blocking_probability_mean']:.3%} "
                f"({delta['blocking_probability_mean_delta'] * 100:+.3f} percentage points)\n"
                f"Mean execution: {greedy['mean_execution_time_mean']:.4f} → "
                f"{randomized['mean_execution_time_mean']:.4f} time units",
                fontsize=12, color="#243447", va="top", linespacing=1.7,
                bbox={"boxstyle": "round,pad=0.6", "facecolor": "#EEF4F8", "edgecolor": "none"})
    for axis, metric, scale, title, ylabel in (
        (axes[0], "blocking_probability", 100, "Blocking probability", "Rejected arrivals (%)"),
        (axes[1], "mean_execution_time", 1, "Accepted-job execution time", "Time units"),
    ):
        for index, seed in enumerate(seeds):
            offset = -0.065 + 0.13 * index / (len(seeds) - 1)
            values = [by_policy[name][seed][metric] * scale for name in ("greedy", "randomized")]
            axis.plot([offset, 1 + offset], values, color="#B4C1CE", alpha=0.55,
                      linewidth=0.9, zorder=1)
            axis.scatter([offset, 1 + offset], values, c=colors, s=30, alpha=0.85, zorder=3)
        upper = max((summaries[name][f"{metric}_mean"] + summaries[name][f"{metric}_sd"]) * scale
                    for name in ("greedy", "randomized"))
        ymax = max(30, math.ceil(upper * 1.12 / 5) * 5) if scale == 100 else max(0.42, upper * 1.12)
        axis.set_ylim(0, ymax)
        for index, name in enumerate(("greedy", "randomized")):
            average = summaries[name][f"{metric}_mean"] * scale
            deviation = summaries[name][f"{metric}_sd"] * scale
            axis.errorbar(index, average, yerr=deviation, fmt="D", color="#172D42",
                          markersize=7, capsize=8, capthick=1.8, elinewidth=1.8, zorder=5)
            label = f"{average:.3f}%" if scale == 100 else f"{average:.6f}"
            axis.text(index, average + deviation + ymax * 0.045, label,
                      ha="center", va="bottom", weight="bold", color="#18334C",
                      bbox={"facecolor": "white", "edgecolor": "none", "pad": 2, "alpha": 0.85})
        axis.set_xlim(-0.35, 1.35)
        axis.set_xticks([0, 1], ["Greedy", "Randomized (paper)"])
        axis.set_title(title, fontsize=13, weight="bold", color="#243447", pad=17)
        axis.set_ylabel(ylabel, labelpad=9)
        axis.yaxis.set_major_locator(MaxNLocator(nbins=5, steps=[1, 2, 5, 10]))
        axis.yaxis.set_major_formatter(FormatStrFormatter("%.0f" if scale == 100 else "%.1f"))
        axis.grid(axis="y", color="#E3EAF0", linewidth=0.8)
        axis.set_axisbelow(True)
    benchmark = data["large_system_execution_benchmark"]
    axes[1].axhline(benchmark, color="#687988", linestyle="--", linewidth=1.3, zorder=2)
    handles = [Line2D([0], [0], color="#B4C1CE", marker="o", markersize=4,
                      label="Paired workload seed"),
               Line2D([0], [0], color="#172D42", marker="D", linestyle="none", markersize=6,
                      label="Mean ±1 SD"),
               Line2D([0], [0], color="#687988", linestyle="--",
                      label=f"Large-system benchmark ({benchmark})")]
    figure.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.53, 0.12),
                  ncol=3, frameon=False, fontsize=10, columnspacing=2)
    figure.text(0.06, 0.095,
                "Small points share arrival times and job sizes; lines connect matching workload seeds.\n"
                "Diamonds show means; bars show ±1 sample standard deviation across seeds, not confidence intervals.\n"
                "Execution time includes accepted jobs only. The dashed benchmark concerns the paper's large-system limit.",
                fontsize=9.5, color="#526579", va="top", linespacing=1.55)
    output = project / "results" / "figures"
    output.mkdir(parents=True, exist_ok=True)
    description = ("M7 matched-workload comparison. Means and one sample SD across seeds. "
                   f"Source: results/policy_comparison.json; SHA256: {hashlib.sha256(source.read_bytes()).hexdigest()}")
    for extension in ("png", "svg"):
        metadata = {"Title": "Greedy vs randomized allocation", "Description": description}
        if extension == "svg":
            metadata["Date"] = None
        figure.savefig(output / f"policy_comparison.{extension}", dpi=300,
                       facecolor="white", metadata=metadata)
        print(f"Saved results/figures/policy_comparison.{extension}")
    plt.close(figure)


if __name__ == "__main__":
    main()
