# CS 176: Social Network Analysis — Project Proposal
**Department of Computer Science, San José State University**  
**Instructor:** Dr. Katerina Potika | **Semester:** Fall 2026  

---

### Project Title:
## Structural Topology, Small-World Dynamics, and Community Partitioning in Modern Cinema Collaboration Networks (2018–2026)

**Student Researcher:** Joel Jacob (Solo Project)  
**Email:** joel.jacob@sjsu.edu  
**Submission Date:** October 2026  

---

### 1. Project Overview & Motivation
Complex social collaboration networks govern creative production in the entertainment industry. While historical social network analyses have investigated classical Hollywood or isolated film productions (e.g., single-movie ego-networks), modern cinema (2018–2026) has experienced structural transformations driven by the expansion of shared cinematic universes (e.g., Marvel, DC), high-budget streaming exclusives (Netflix, Apple TV+, Amazon MGM), and prestige auteur circuits (A24, Neon).

This project investigates the social topology of modern film collaboration by constructing an **actor-to-actor collaboration network** from global feature films released between 2018 and 2026. By mapping co-starring affiliations, we aim to uncover how casting cliques form, identify the structural "bridge actors" who connect disparate cinematic genres and franchises, quantify the empirical "Six Degrees of Kevin Bacon" small-world effect in contemporary cinema, and compare divisive (Girvan–Newman) versus agglomerative (Louvain) community detection algorithms on real-world creative networks.

---

### 2. Dataset Provenance & Network Extraction Pipeline

#### 2.1 Data Sources
The primary data will be acquired from official, non-commercial public interfaces:
1. **IMDb Official Non-Commercial Interfaces:**
   * URL: [https://datasets.imdbws.com/](https://datasets.imdbws.com/)
   * Primary tables: `title.basics.tsv.gz` (metadata: title, release year, runtime, primary genres), `title.principals.tsv.gz` (cast and crew roles with billing ordering), and `name.basics.tsv.gz` (actor names and primary professions).
2. **The Movie Database (TMDB) API & Public Cinema Interfaces:**
   * Used for cross-referencing worldwide box-office rankings and critical acclaim filters to focus on widely released feature films.

#### 2.2 Network Construction & Bipartite Projection
Raw cinematic data represents a **bipartite affiliation network** $B = (V_A \cup V_M, E_B)$, where $V_A$ represents actors, $V_M$ represents feature films, and an edge exists between an actor and a movie if the actor appeared in that production.

To focus on peer collaboration dynamics, we perform a unipartite **bipartite projection onto the actor partition**:
* **Nodes ($V$):** Professional actors who starred in feature films released from 2018 to 2026. To eliminate peripheral noise and uncredited cameos while preventing unmanageable clique explosions, we filter to the top 4–6 principal billed actors per film.
* **Edges ($E$):** Co-starring interactions. An undirected edge $e = (u, v)$ exists if actor $u$ and actor $v$ co-starred in at least one feature film within the evaluation window.
* **Edge Weights ($W$):** An integer weight $w(u, v) \ge 1$ denoting the total number of shared feature film productions, directly operationalizing Granovetter's tie strength.
* **Target Network Scale:** Approximately **1,800 to 2,500 actor nodes** and **6,000 to 12,000 collaboration edges**. This sweet spot provides high structural richness and non-trivial community partitions while guaranteeing fast, exact calculation of all-pairs shortest paths, diameters, and iterative edge-betweenness centrality in NetworkX.
* **Export Artifact:** A standardized `.graphml` file encoding node attributes (actor name, primary genres, film count) and edge attributes (weight, titles of shared films).

---

### 3. Knowledge to Gain & Research Hypotheses

We frame the analysis around four testable research questions grounded in network science and the CS 176 curriculum:

#### Research Question 1: Small-World Topology & Empirical Bacon Numbers (Lecture 3)
* **Question:** Does modern cinema continue to exhibit small-world network properties despite franchise fragmentation and streaming silos?
* **Hypothesis:** We hypothesize that the actor network forms a **Small-World Network** (Watts & Strogatz, 1998), characterized by a high average clustering coefficient ($C_{\text{empirical}} \gg C_{\text{random}}$) alongside an average path length $L$ scaling logarithmically with network size ($L \sim \ln |V|$). We will measure the network diameter $D$ and average shortest path length across the giant connected component to quantify the modern equivalent of the "Bacon Number."

#### Research Question 2: Structural "Bridge Actors" via Betweenness Centrality (Lecture 2)
* **Question:** Which actors act as global structural bridges across Hollywood, and does high betweenness correlate with high degree (total co-stars)?
* **Hypothesis:** High betweenness centrality ($C_B(v)$) will not be dominated strictly by superstar franchise leads (who tend to stay inside dense franchise cliques). Instead, the highest betweenness nodes will be versatile character actors who cross boundaries between blockbuster IP franchises (Marvel, Star Wars) and prestige indie cinema (A24, Focus Features), serving as structural weak-tie bridges across disparate casting communities.

#### Research Question 3: Triadic Closure within Franchise Ensembles (Lecture 3 & 4)
* **Question:** Do recurring ensemble productions create localized cliques with maximum clustering coefficients?
* **Hypothesis:** Cast members of multi-film franchises and recurring ensembles (e.g., *Avengers*, *Dune*, *Knives Out*, *Fast & Furious*) will exhibit local clustering coefficients approaching $C_i \to 1.0$ due to strong triadic closure, whereas character actors spanning unconnected independent productions will have significantly lower clustering coefficients and broader neighborhood diversity.

#### Research Question 4: Community Partitioning & Genre/Studio Homophily (Activity 2)
* **Question:** How do divisive (Girvan–Newman) and agglomerative (Louvain) community detection algorithms partition the Hollywood social landscape?
* **Hypothesis:** Community detection will recover distinct, interpretable production clusters (e.g., Superhero/Sci-Fi Blockbuster clique, British/European Period Drama clique, Comedy/Indie circuit). Girvan–Newman's iterative removal of maximum edge-betweenness bridges will systematically sever the inter-franchise connecting actors first, demonstrating the structural separation of Hollywood creative sub-economies.

---

### 4. Proposed Network Characterization & Algorithmic Plan

In strict accordance with Step 2 of the project specifications, we will compute and report:
1. **Total Number of Nodes ($|V|$):** Number of unique principal actors in the network.
2. **Total Number of Edges ($|E|$):** Number of unique co-starring collaboration pairs.
3. **Connected Components:** Total count and size distribution of connected components, explicitly isolating the **Giant Connected Component (GCC)**.
4. **Network Diameter:** The longest shortest path distance $\max_{u, v \in V_{\text{GCC}}} d(u, v)$, computed across the GCC.
5. **Top 5 Nodes by Clustering Coefficient:** Identification of the five actors with the highest local clustering coefficients $C_i = \frac{2 e_i}{k_i(k_i - 1)}$, with explicit tie-breaking criteria.
6. **Top 5 Nodes by Betweenness Centrality:** Identification of the five actors with highest Freeman node betweenness centrality $C_B(v) = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$.
7. **Algorithmic Implementation — Girvan–Newman with Tie-Breaking:**
   * A Python implementation iteratively calculating edge betweenness centrality:
     $$C_B(e) = \sum_{s \neq t} \frac{\sigma_{st}(e)}{\sigma_{st}}$$
   * At each iteration, the edge with the maximum edge betweenness is deleted. If multiple edges tie for the maximum value, ties are broken deterministically.
   * Edge removals will be logged until the giant component splits into distinct components, tracking modularity score $Q$ at each step and comparing the final partition against the **Louvain modularity maximization** algorithm.

---

### 5. Visualization Plan (Step 3)

We will construct high-resolution, colorized network visualizations using NetworkX and Matplotlib:
* **Global Network Topology:** A force-directed layout (Spring layout with tuned Fruchterman–Reingold parameters) colored by detected Louvain / Girvan–Newman community partitions.
* **Centrality Mapping:** Node diameters will be scaled dynamically according to betweenness centrality, visually highlighting the key "bridge actors."
* **Bridge Edge Highlighting:** Intra-community edges will be rendered in vibrant community colors, while inter-community bridge edges identified by Girvan–Newman will be highlighted in dark slate gray (`#333333`) to visually isolate casting fault lines.

---

### 6. Deliverables & Project Roadmap

| Phase | Milestone Description | Target Output |
| :--- | :--- | :--- |
| **Phase 1** | Dataset curation, web extraction script, and bipartite projection | `build_cinema_network.py`, `cinema_network.graphml` |
| **Phase 2** | Network characterization, metric calculations, and top-5 rankings | `Characterization.ipynb`, characterization table |
| **Phase 3** | Girvan–Newman divisive loop, modularity tracking, and Louvain | Community partitions, modularity $Q$ logs, `communities.txt` |
| **Phase 4** | High-resolution visual renderings and layout tuning | Multi-color PNG/SVG network visualization figures |
| **Phase 5** | Final Comprehensive Project Report ($\le 10$ pages) | `CS176_Final_Report_Joel_Jacob.pdf` |

---

### 7. References
1. **Watts, D. J., & Strogatz, S. H. (1998).** Collective dynamics of 'small-world' networks. *Nature*, 393(6684), 440-442.
2. **Girvan, M., & Newman, M. E. (2002).** Community structure in social and biological networks. *Proceedings of the National Academy of Sciences*, 99(12), 7821-7826.
3. **Blondel, V. D., et al. (2008).** Fast unfolding of communities in large networks. *Journal of Statistical Mechanics: Theory and Experiment*, 2008(10), P10008.
4. **Granovetter, M. S. (1973).** The strength of weak ties. *American Journal of Sociology*, 78(6), 1360-1380.
5. **IMDb Datasets Documentation.** Non-commercial data access. [https://datasets.imdbws.com/](https://datasets.imdbws.com/).
