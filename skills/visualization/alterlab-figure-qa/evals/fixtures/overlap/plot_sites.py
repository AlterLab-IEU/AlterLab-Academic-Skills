"""Plant species richness per survey site, 2024 vs 2025 (Aegean upland grassland survey)."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv("site_richness.csv")
sites = list(dict.fromkeys(df["site"]))
x = range(len(sites))

fig, ax = plt.subplots(figsize=(7.0, 3.0))
for year, marker in [(2024, "o"), (2025, "s")]:
    sub = df[df["survey_year"] == year].set_index("site").loc[sites]
    ax.plot(x, sub["species_richness"], marker=marker, ls="none", ms=6, label=f"{year} survey")

ax.set_xticks(list(x))
ax.set_xticklabels(sites, fontsize=8)
ax.set_ylim(0, 50)
ax.set_ylabel("Species richness (per 6 transects)", fontsize=8)
ax.legend(loc="upper right", fontsize=8, framealpha=1)
fig.tight_layout()
fig.savefig("fig_sites.png", dpi=300, metadata={"Software": None})
