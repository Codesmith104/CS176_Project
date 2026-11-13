# CS 176: Social Network Analysis — Project Progress Report
**Instructor:** Dr. Katerina Potika | **Semester:** Fall 2026 | **Department of Computer Science, SJSU**

## Modern Cinema Collaboration Network: Small-World Dynamics, Structural Bridges, and Community Partitioning (2018–2026)

**Student Researcher:** Joel Jacob (Solo Project) | **Email:** joel.jacob@sjsu.edu  
**Milestone Date:** November 2026  

---

### 1. Executive Summary & Project Status
This progress report details the completion of Step 1 (Web Data Extraction and GraphML Network Construction), preliminary Step 2 (Network Characterization), and Step 3 (Network Visualization) for the Modern Cinema Collaboration Network project.

The research investigates the social topology of contemporary cinema (2018–2026), analyzing casting community modularity, empirical small-world properties, and vertex centrality distributions. All pipeline components were implemented in Python using NetworkX and SciPy (`build_cinema_network.py`).

| Milestone Phase | Assignment Step | Target Deliverable | Current Status |
| :--- | :--- | :--- | :---: |
| **Phase 1: Data Pipeline** | Step 1: Web Network Creation | `build_cinema_network.py`, `cinema_network.graphml` | **100% Completed** |
| **Phase 2: Characterization** | Step 2: Baseline Metrics & Top-5 | Baseline metrics computed; GCC isolated | **80% Completed** |
| **Phase 3: Community Algorithm** | Step 2: Girvan-Newman Loop | Divisive edge-betweenness loop & Louvain benchmark | **In Progress** |
| **Phase 4: Network Visualization**| Step 3: Visualization & Plots | `preliminary_network.png` (high-res spring layout) | **75% Completed** |
| **Phase 5: Final Report** | Step 4: Final Summary Report | Comprehensive final report (<= 10 pages) | **Scheduled** |

---

### 2. Step 1 Completion: Data Pipeline & GraphML Model
Data acquisition encompassed 1,634 feature films released between 2018 and 2026. The source data forms a bipartite affiliation network connecting film titles to cast members.

#### Bipartite-to-Unipartite Projection
To analyze peer collaboration dynamics, the bipartite structure was projected into an undirected, weighted unipartite collaboration graph G = (V, E, W):
* **Vertices (V):** Professional actors in distributed feature films. To isolate principal collaborators and prevent combinatorial clique expansion, only the top 4 billed actors per film were retained.
* **Edges (E) and Weights (W):** An undirected edge (u, v) denotes shared billing in at least one feature film. The integer weight w(u, v) >= 1 quantifies co-occurrence frequency, serving as an operational proxy for tie strength.
* **GraphML Serialization:** The network was exported to `cinema_network.graphml` (1.7 MB), embedding vertex attributes (actor identifier, title count, primary genre) and edge weights.

---

### 3. Step 2 Progress: Baseline Network Characterization
Network metrics were computed across both the global graph and its Giant Connected Component (GCC) using NetworkX.

#### Table 1: Empirical Network Metrics

| Metric / Dimension | Full Network Value | Giant Connected Component (GCC) | Assignment Reference |
| :--- | :---: | :---: | :--- |
| **Total Nodes (V)** | 3,296 vertices | 2,774 vertices (84.16% of network) | Step 2.1: Node count |
| **Total Edges (E)** | 8,602 edges | 7,885 collaboration ties | Step 2.2: Edge count |
| **Connected Components** | 143 components | 1 component (2nd largest: 7 vertices) | Step 2.3: Components |
| **Network Density** | 0.001584 | 0.002050 | Global network sparsity |
| **Average Clustering (C)** | 0.7235 | 0.6887 | Step 2.5: Triadic closure |
| **Network Diameter (D)** | — (disconnected) | **13** | Step 2.4: Longest shortest path |
| **Average Path Length (L)**| — (disconnected) | **5.096** ("Bacon Number") | Small-world path distance |
| **Louvain Modularity (Q)** | — | **0.6561** (33 communities) | Step 2.7: Modularity score |

#### Empirical Interpretations & Centrality Rankings
1. **Validation of Small-World Architecture:**  
   The GCC exhibits a pronounced clustering coefficient (C = 0.6887) alongside a short average path length (L = 5.096) and a diameter of 13. This empirically validates Watts-Strogatz small-world behavior: despite containing 2,774 connected actors, any arbitrary pair is separated by an average of five collaboration hops.
2. **Top-5 Vertices by Degree Centrality:**  
   Bruce Willis (45 co-stars, 29 films), Frank Grillo (37 co-stars, 14 films), Lil Rel Howery (34 co-stars, 12 films), Margot Robbie (32 co-stars, 11 films), Tiffany Haddish (32 co-stars, 11 films).
3. **Top-5 Vertices by Betweenness Centrality (GCC Structural Bridges):**  
   Bruce Willis (C_B = 0.04464), Frank Grillo (C_B = 0.03760), Lil Rel Howery (C_B = 0.02942), Tiffany Haddish (C_B = 0.02760), Ryan Reynolds (C_B = 0.02724).  
   *Analysis:* Betweenness centrality isolates versatile actors bridging distinct studio and genre boundaries (e.g., Ryan Reynolds, Margot Robbie, and Tiffany Haddish connecting major studio franchises, independent productions, and streaming releases).
4. **Top-5 Vertices by Clustering Coefficient (Degree >= 5):**  
   Spencer Locke, Danai Gurira, Michael Greyeyes, Chaske Spencer, Dan Fogler (each C_i = 0.6000).  
   *Analysis:* High clustering identifies recurring ensemble casts (e.g., Danai Gurira in the Marvel ensemble, Dan Fogler in *Fantastic Beasts*) operating within dense, highly interconnected cliques.

---

### 4. Step 3 Progress: Preliminary Network Visualization
A high-resolution network visualization was rendered in NetworkX (`preliminary_network.png`, 1.8 MB) using a force-directed Fruchterman-Reingold spring layout.

* **Core Subnetwork Isolation:** To avoid graph density occlusion while preserving macro-topological structure, the top 250 vertices by degree within the GCC were visualized along with their interconnecting edges.
* **Visual Encodings:**
  * **Vertex Radii:** Scaled proportionally to Freeman betweenness centrality (C_B), visually magnifying pivotal bridge actors.
  * **Vertex Color:** Mapped to modular community assignments identified by the Louvain algorithm (Q = 0.6561 across 33 communities).
  * **Edge Representation:** Semi-transparent lines (#7f8c8d) highlight density variations between intra-community ties and cross-community bridges.
* **Topological Observations:** The layout demonstrates clear community segregation corresponding to franchise productions, held together by high-betweenness vertices acting as structural bridges.

---

### 5. Remaining Roadmap & Path to Final Submission
Remaining project tasks focus on divisive algorithm execution and formal synthesis:

1. **Girvan-Newman Divisive Algorithm (Step 2.7):** Implement the iterative edge-betweenness removal loop on a representative community subgraph, removing edges with maximum betweenness C_B(e) with deterministic tie-breaking, logging partition modularity Q at each stage.
2. **Algorithmic Comparison:** Contrast the divisive hierarchical clustering of Girvan-Newman against the agglomerative modularity optimization of Louvain, analyzing partition resolution, runtime, and modularity tradeoffs.
3. **Advanced Visualization:** Construct comparative multi-panel figures highlighting severed bridge edges (#333333) and community subgraphs.
4. **Final Comprehensive Report (Step 4):** Synthesize empirical findings, algorithmic evaluations, and visualization figures into the final submission report (<= 10 pages).
