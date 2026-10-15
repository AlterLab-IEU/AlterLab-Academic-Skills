"""Figure 2: growth of E. coli K-12 oxidative-stress mutants in LB + 0.5 mM H2O2."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv("growth_curves.csv")

fig, ax = plt.subplots(figsize=(3.5, 2.6))  # single journal column
for strain, sub in df.groupby("strain", sort=False):
    ax.errorbar(sub["time_h"], sub["od600_mean"], yerr=sub["od600_sd"],
                marker="o", ms=3, lw=1, capsize=2, label=strain)

ax.set_xlim(0, 20)
ax.set_ylim(0, 1.7)
ax.set_xlabel("Time (h)", fontsize=7)
ax.set_ylabel("OD$_{600}$", fontsize=7)
ax.tick_params(labelsize=4)
ax.legend(fontsize=6, frameon=False, loc="lower right")
fig.tight_layout()
fig.savefig("fig2_growth.png", dpi=150, metadata={"Software": None})
