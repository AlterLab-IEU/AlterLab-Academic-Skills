"""Dose-response of three kinase inhibitors in A549 cells (72 h, CellTiter-Glo, n = 4)."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv("dose_response.csv")

fig, ax = plt.subplots()
for name, sub in df.groupby("compound"):
    ax.errorbar(sub["conc_uM"], sub["response_pct"], yerr=sub["sem"],
                marker="o", capsize=3, label=name)
ax.set_xscale("log")
ax.set_xlabel("Concentration (uM)")
ax.set_ylabel("Viability (% of DMSO control)")
ax.set_title("Dose response")
ax.legend()
fig.savefig("dose_response.png", metadata={"Software": None})
