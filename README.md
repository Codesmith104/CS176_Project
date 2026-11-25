# Modern Cinema Collaboration Network: Small-World Dynamics, Structural Bridges, and Community Partitioning (2018–2023)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Codesmith104/CS176_Project/blob/main/Cinema_Network_Analysis.ipynb)

---

## Project Overview
Creative collaboration in the film industry is structured by complex social dynamics. This project investigates the social topology of contemporary American feature cinema (2018–2023) by constructing an actor-to-actor collaboration network from Wikipedia feature film records ([prust/wikipedia-movie-data](https://github.com/prust/wikipedia-movie-data)).

We evaluate:
1. **The Small-World Phenomenon ("Six Degrees of Kevin Bacon"):** Testing whether modern cinema maintains low diameter and short average path length under contemporary casting dynamics.
2. **Structural "Bridge Actors" via Betweenness Centrality:** Identifying prolific actors and brokers spanning disparate casting clusters.
3. **Ensemble Cliques & Triadic Closure:** Measuring localized clustering coefficients across recurring co-starring ensembles.
4. **Community Detection & Partitioning:** Comparing agglomerative (Louvain) and divisive (Girvan–Newman) community detection algorithms.
5. **Link Prediction via Train/Test Split:** Evaluating topological heuristics (Jaccard, Adamic–Adar, Resource Allocation, and Preferential Attachment) using ROC-AUC scores to predict future casting collaborations.
6. **Multi-Technique Visualizations:** High-resolution force-directed network plots, divisive decomposition panels, and statistical property/ROC curves.

---

## Empirical Network Characteristics
The network was constructed by projecting a bipartite affiliation network of 1,634 feature films (2018–2023) into an undirected, weighted unipartite collaboration graph $G = (V, E, W)$, retaining the top 4 principal billed actors per film:

* **Total Vertices ($|V|$):** 3,296 actors
* **Total Edges ($|E|$):** 8,602 co-starring pairs (`8,435` single-film weak ties / `98.06%`; `167` repeat strong ties / `1.94%`)
* **Connected Components:** 143 components
* **Giant Connected Component (GCC):** 2,774 actors (84.16% of total network), 7,885 edges
* **Network Density ($\rho$):** 0.001584 (GCC: 0.002050)
* **Average Clustering Coefficient ($C$):** 0.7235 (GCC: 0.6887)
* **GCC Network Diameter ($D$):** 13 hops
* **GCC Average Shortest Path Length ($L$):** 5.096 hops ("Bacon Number")
* **Louvain Modularity ($Q$):** 0.6561 across 33 communities

### Top-5 Centrality Highlights
* **Degree Centrality:** Bruce Willis (45), Frank Grillo (37), Lil Rel Howery (34), Margot Robbie (32), Tiffany Haddish (32).
* **Betweenness Centrality ($C_B$ in GCC):** Bruce Willis (0.04464), Frank Grillo (0.03760), Lil Rel Howery (0.02942), Tiffany Haddish (0.02760), Ryan Reynolds (0.02724).
* **Clustering ($C_i$, Degree $\ge 5$):** Spencer Locke, Danai Gurira, Michael Greyeyes, Chaske Spencer, Dan Fogler (each 0.6000).

### Girvan-Newman Divisive Community Splits (Community $C_0$, 139 Nodes, 292 Edges)
Iteratively removing edges with maximum edge betweenness $C_B(e)$ decomposes the primary casting community ($C_0$) into five sub-clusters, progressively increasing modularity:
* **Split 1 (Step 12):** Removed `('Kevin Hart', 'Mark Wahlberg')` (*Me Time*, $C_B = 0.3326$) $\to$ 2 components `[110, 29]`, $Q = 0.2711$
* **Split 2 (Step 23):** Removed `('Elizabeth Olsen', 'Benedict Wong')` (*Doctor Strange in the Multiverse of Madness*, $C_B = 0.3116$) $\to$ 3 components `[61, 49, 29]`, $Q = 0.5546$
* **Split 3 (Step 30):** Removed `('Hugh Jackman', 'Zach Galifianakis')` (*Missing Link*, $C_B = 0.0532$) $\to$ 4 components `[51, 49, 29, 10]`, $Q = 0.5854$
* **Split 4 (Step 36):** Removed `('Gabriel LaBelle', 'Seth Rogen')` (*The Fabelmans*, $C_B = 0.0436$) $\to$ 5 components `[51, 38, 29, 11, 10]`, $Q = 0.6089$

### Link Prediction Benchmark (Train/Test Split)
Evaluated across 500 held-out positive test edges and 500 negative non-edges ($N = 1,000$ pairs):
* **Jaccard Coefficient:** $\text{ROC-AUC} = \mathbf{0.9852}$
* **Adamic-Adar Index:** $\text{ROC-AUC} = \mathbf{0.9851}$
* **Resource Allocation Index:** $\text{ROC-AUC} = \mathbf{0.9851}$
* **Preferential Attachment:** $\text{ROC-AUC} = \mathbf{0.6264}$

**Top Predicted Future Collaborations (Adamic-Adar):**
1. **Tessa Thompson & Zazie Beetz** (Score: 1.660 | Shared: *André Holland*, *Armie Hammer*, *Jonathan Majors*)
2. **Ryan Reynolds & Ben Affleck** (Score: 1.211 | Shared: *Gal Gadot*, *Jodie Comer*, *Lil Rel Howery*)
3. **Bruce Willis & Jessica Chastain** (Score: 1.194 | Shared: *James McAvoy*, *John Malkovich*, *Vincent D'Onofrio*)
4. **Jon Hamm & Anthony Mackie** (Score: 1.141 | Shared: *David Harbour*, *Jamie Dornan*, *Marcia Gay Harden*)
5. **Tiffany Haddish & Casey Affleck** (Score: 1.127 | Shared: *Christopher Abbott*, *Elisabeth Moss*, *Tika Sumpter*)

---

## Repository Structure
```text
├── README.md                              # Project documentation and empirical summary
├── Cinema_Network_Analysis.ipynb          # Interactive, pre-executed Google Colab notebook
├── build_cinema_network.py                # Complete pipeline: ingestion, metrics, GN, LP, figures
├── cinema_network.graphml                 # Serialized network artifact (GraphML format, 1.7 MB)
├── movies_cache.json                      # Cached Wikipedia movie metadata (2018-2023 feature subset)
├── preliminary_network.png                # Figure 1: Connected 115-node core topology (300 DPI)
├── figure1_network_topology.png           # Figure 1 copy for reference (300 DPI)
├── figure2_girvan_newman_splits.png       # Figure 2: Girvan-Newman divisive decomposition (300 DPI)
└── figure3_network_distributions.png      # Figure 3: Degree, weight, betweenness, and ROC curves (300 DPI)
```

---

## Reproduction & Setup

### Prerequisites
* Python 3.10+
* [uv](https://github.com/astral-sh/uv) (recommended) or standard `pip`

### Dependencies
* `networkx`
* `matplotlib`
* `scikit-learn`
* `numpy`

### Execution
Run the complete end-to-end pipeline:
```bash
uv run --with networkx --with matplotlib --with scikit-learn --with numpy python build_cinema_network.py
```
This script will:
1. Load or fetch the feature film dataset (`2018–2023`, 1,634 films).
2. Project and build the undirected weighted actor collaboration graph $G = (V, E, W)$.
3. Export the network artifact to `cinema_network.graphml`.
4. Calculate and display all characterization metrics and top centrality rankings.
5. Execute the Girvan-Newman divisive algorithm and log bridge edge removals.
6. Execute the Link Prediction train/test split benchmark and compute ROC-AUC scores.
7. Render and save all high-resolution figures at 300 DPI.

### Interactive Google Colab
Launch the analysis notebook directly in your browser:
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Codesmith104/CS176_Project/blob/main/Cinema_Network_Analysis.ipynb)
