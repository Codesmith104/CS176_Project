# CS 176: Social Network Analysis — Project Proposal
**Instructor:** Dr. Katerina Potika | **Semester:** Fall 2026 | **Department of Computer Science, SJSU**

## Modern Cinema Collaboration Network: Small-World Dynamics, Structural Bridges, and Community Partitioning (2018–2026)

**Student Researcher:** Joel Jacob (Solo Project) | **Email:** joel.jacob@sjsu.edu

---

### 1. Project Overview & Motivation
Creative collaboration in the film industry is governed by complex social dynamics. While classical network studies examined historical Hollywood or isolated single-film ego-networks, contemporary cinema (2018–2026) has been fundamentally transformed by shared franchise universes (Marvel, DC), major streaming studio exclusives (Netflix, Apple TV+), and prestige independent circuits (A24, Neon).

This project investigates the social topology of modern film production by constructing an actor-to-actor collaboration network from global feature films released between 2018 and 2026. By analyzing co-starring affiliations, we aim to quantify the small-world phenomenon in modern cinema, identify the structural "bridge actors" who connect disparate genres, and evaluate how casting communities partition across creative sub-economies.

### 2. Dataset & Network Model
* **Data Sources:** Official IMDb non-commercial datasets (datasets.imdbws.com) using `title.basics.tsv.gz` (release years, genres), `title.principals.tsv.gz` (cast billing positions), and `name.basics.tsv.gz` (actor identities), cross-referenced with TMDB box-office lists.
* **Network Construction:** Bipartite actor-movie affiliation data is projected into an undirected, weighted unipartite actor collaboration graph G = (V, E, W):
  * **Nodes (V):** Professional actors starring in widely released feature films (2018–2026). To eliminate peripheral cameos and avoid artificial clique inflation, we retain the top 4–6 billed principal actors per film.
  * **Edges (E) & Weights (W):** An undirected edge (u, v) exists if actors u and v co-starred in at least one feature film. The integer weight w(u, v) >= 1 represents the total number of shared productions, quantifying collaboration tie strength.
  * **Target Scale & Export:** ~1,800 to 2,500 actors and ~6,000 to 10,000 edges. This size is statistically robust while allowing exact computation of shortest paths, diameter, and edge-betweenness centrality in NetworkX. The network will be exported to a standardized `.graphml` file containing actor metadata (genres, film counts) and edge collaboration weights.

### 3. Knowledge to Gain & Research Questions
We center our investigation on four key research questions grounded in network science:

1. **The Modern "Six Degrees of Kevin Bacon" (Small-World Topology):** Does contemporary cinema preserve the small-world property despite franchise fragmentation? We will compute the network diameter D and average shortest path length L on the giant connected component, testing the hypothesis that empirical clustering is significantly higher than a random graph (C_empirical >> C_random) with logarithmic path scaling (L ~ ln(|V|)).
2. **Structural "Bridge Actors" via Betweenness Centrality:** Which actors possess the highest Freeman betweenness centrality (C_B), and does betweenness correlate with total degree? We hypothesize that top betweenness nodes are not solely franchise leads, but versatile character actors who cross boundaries between major blockbuster franchises and prestige indie cinema, acting as weak-tie bridges.
3. **Franchise Cliques and Triadic Closure:** Do recurring ensemble productions produce localized clusters with maximum clustering coefficients? We hypothesize that recurring ensembles (Avengers, Dune, Knives Out) form near-complete cliques (C_i -> 1.0) through strong triadic closure, whereas actors with diverse filmographies exhibit lower clustering and higher neighborhood diversity.
4. **Community Detection & Genre/Studio Homophily:** How do divisive (Girvan–Newman) and agglomerative (Louvain) community detection algorithms partition the Hollywood collaboration network? We hypothesize that the network partitions naturally into interpretable genre and production clusters (e.g., Superhero Blockbuster, British Drama, Indie/Comedy circuits), with Girvan–Newman's edge removals systematically severing the inter-franchise bridge actors.

### 4. Planned Characterization & Deliverables
In accordance with the assignment guidelines, our analysis pipeline will compute:
* **Network Metrics:** Total nodes (|V|), total edges (|E|), connected components, and network diameter on the giant connected component.
* **Top-5 Rankings:** Five nodes with the highest clustering coefficients and five nodes with the highest betweenness centrality (with deterministic tie-breaking).
* **Algorithmic Analysis:** Custom implementation of the Girvan–Newman algorithm iteratively removing edges with maximum edge betweenness C_B(e) with deterministic tie-breaking, logging modularity score Q and comparing results against the Louvain algorithm.
* **Visualizations & Report:** High-resolution force-directed network plots with nodes colored by community, node sizes scaled by betweenness centrality, and bridge edges highlighted in `#333333`. All results will be synthesized in a final comprehensive report (<= 10 pages).
