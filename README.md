# Modern Cinema Collaboration Network: Small-World Dynamics, Structural Bridges, and Community Partitioning (2018–2026)

**Name:** Joel

---

## 📌 Project Overview
Creative collaboration in the film industry is structured by complex social dynamics. This project investigates the social topology of contemporary cinema (2018–2026) by constructing an actor-to-actor collaboration network from global feature films.

We evaluate:
1. **The Small-World Phenomenon ("Six Degrees of Kevin Bacon"):** Testing whether modern cinema maintains low diameter and short average path length despite streaming and franchise fragmentation.
2. **Structural "Bridge Actors" via Betweenness Centrality:** Identifying versatile actors who bridge independent prestige cinema and major studio franchises.
3. **Franchise Cliques & Triadic Closure:** Measuring localized clustering coefficients across recurring ensemble casts.
4. **Community Detection & Studio Homophily:** Comparing divisive (Girvan–Newman) and agglomerative (Louvain) community detection algorithms.

---

## 📊 Empirical Network Characteristics
The network was constructed by projecting a bipartite affiliation network of 1,634 feature films into an undirected, weighted unipartite collaboration graph $G = (V, E, W)$, retaining the top 4 principal billed actors per film:

* **Total Vertices ($|V|$):** 3,296 actors
* **Total Edges ($|E|$):** 8,602 co-starring pairs
* **Connected Components:** 143 components
* **Giant Connected Component (GCC):** 2,774 actors (84.16% of total network), 7,885 edges
* **Network Density:** 0.001584 (GCC: 0.002050)
* **Average Clustering Coefficient ($C$):** 0.7235 (GCC: 0.6887)
* **GCC Network Diameter ($D$):** 13 hops
* **GCC Average Shortest Path Length ($L$):** 5.096 hops ("Bacon Number")
* **Louvain Modularity ($Q$):** 0.6561 across 33 communities

### Top-5 Centrality Highlights:
* **Degree Centrality:** Bruce Willis (45), Frank Grillo (37), Lil Rel Howery (34), Margot Robbie (32), Tiffany Haddish (32).
* **Betweenness Centrality ($C_B$):** Bruce Willis (0.04464), Frank Grillo (0.03760), Lil Rel Howery (0.02942), Tiffany Haddish (0.02760), Ryan Reynolds (0.02724).
* **Clustering ($C_i$, Degree $\ge$ 5):** Spencer Locke, Danai Gurira, Michael Greyeyes, Chaske Spencer, Dan Fogler (each 0.6000).

---

## 📂 Repository Structure
```text
├── README.md                      # Project documentation and summary
├── .gitignore                     # Excludes cache and archive files
├── build_cinema_network.py        # Pipeline script: data extraction, graph building, metrics
├── cinema_network.graphml         # Generated network artifact (GraphML format, 1.7 MB)
├── preliminary_network.png        # High-resolution network visualization (300 DPI)
├── Project_Proposal_1-2pages.md   # Milestone 1: Approved 1-2 page proposal
├── Project_Progress_Report.md     # Milestone 2: 2-3 page formal progress report
└── directions.txt                 # Course assignment instructions and guidelines
```

---

## 🚀 Reproduction & Setup

### Prerequisites
* Python 3.10+
* [uv](https://github.com/astral-sh/uv) (recommended) or standard `pip`

### Dependencies
* `networkx`
* `matplotlib`
* `scipy`

### Execution
Run the full network construction and analysis pipeline using `uv`:
```bash
uv run --with networkx --with matplotlib --with scipy python build_cinema_network.py
```
This script will:
1. Load or fetch the feature film dataset (2018–2026).
2. Project and build the actor collaboration graph.
3. Export the network artifact to `cinema_network.graphml`.
4. Calculate and display all characterization metrics.
5. Render and save the high-resolution visualization to `preliminary_network.png`.
