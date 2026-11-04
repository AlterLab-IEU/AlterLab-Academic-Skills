"""Figure 4B: HepG2 viability over 7 days under Drug A / Drug B (CellTiter-Glo, n = 3 wells)."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ORDER = ["Vehicle", "Drug A 1 uM", "Drug A 10 uM", "Drug B 10 uM"]

df = pd.read_csv("viability_timecourse.csv")
df = df[df["treatment"].isin(ORDER)]          # keep the four arms, drop the pilot wells

fig, ax = plt.subplots(figsize=(3.5, 2.6))
for trt, sub in df.groupby("treatment", sort=False):
    sub = sub.sort_values("day")
    ax.errorbar(sub["day"], sub.iloc[:, 2],     # column 2 = mean viability
                yerr=sub["viability_sem"], marker="o", ms=3, lw=1, capsize=2, label=trt)

ax.set_xlabel("Day", fontsize=8)
ax.set_ylabel("Cell viability (%)", fontsize=8)
ax.set_ylim(0, 105)
ax.tick_params(labelsize=7)
ax.legend(fontsize=6, frameon=False, loc="upper left")
fig.tight_layout()
fig.savefig("fig4b_viability.png", dpi=300, metadata={"Software": None})
