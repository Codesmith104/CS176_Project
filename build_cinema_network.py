#!/usr/bin/env python3
"""
CS 176: Social Network Analysis — Step 1 Data Pipeline & Network Construction
Script: build_cinema_network.py
Author: Joel Jacob (Solo Project)
Description:
    Constructs an undirected, weighted unipartite collaboration network of modern cinema (2018-2026).
    Extracts top 4 billed actors per feature film, computes tie weights based on co-starring frequency,
    exports the network to GraphML format, and outputs preliminary characterization metrics.
"""

import urllib.request
import json
import itertools
import time
import os
import networkx as nx
import networkx.algorithms.community as nx_comm
import matplotlib.pyplot as plt

def load_modern_movies():
    cache_file = "/Users/joelj/Class_Stuff/176/Project/movies_cache.json"
    if os.path.exists(cache_file):
        print(f"Loading cached movie dataset from {cache_file}...")
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        url = "https://raw.githubusercontent.com/prust/wikipedia-movie-data/master/movies.json"
        print(f"Fetching movie dataset from {url}...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
        print(f"Cached {len(data)} movies to {cache_file}.")

    # Filter for modern cinema feature films (2018 onwards)
    modern_movies = [m for m in data if m.get("year", 0) >= 2018 and len(m.get("cast", [])) >= 2]
    print(f"Extracted {len(modern_movies)} modern feature films (2018-2026).")
    return modern_movies

def construct_collaboration_network(movies, max_billing=4):
    print(f"Constructing actor collaboration graph (top {max_billing} billed actors per film)...")
    G = nx.Graph()

    for m in movies:
        cast = [actor.strip() for actor in m.get("cast", [])[:max_billing] if actor.strip()]
        title = m.get("title", "Unknown")
        year = m.get("year", 0)
        genres = ", ".join(m.get("genres", []))

        # Add or update actor nodes
        for actor in cast:
            if not G.has_node(actor):
                G.add_node(actor, film_count=1, sample_films=title, primary_genre=genres.split(", ")[0] if genres else "Drama")
            else:
                G.nodes[actor]["film_count"] += 1
                sample = G.nodes[actor]["sample_films"].split("; ")
                if len(sample) < 4 and title not in sample:
                    G.nodes[actor]["sample_films"] += "; " + title

        # Add or update undirected collaboration edges
        for u, v in itertools.combinations(cast, 2):
            if G.has_edge(u, v):
                G[u][v]["weight"] += 1
                shared = G[u][v]["movies"].split("; ")
                if title not in shared:
                    G[u][v]["movies"] += "; " + title
            else:
                G.add_edge(u, v, weight=1, movies=title)

    print(f"Graph constructed: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges.")
    return G

def export_graphml(G, filepath="/Users/joelj/Class_Stuff/176/Project/cinema_network.graphml"):
    print(f"Exporting network to GraphML format: {filepath}...")
    nx.write_graphml(G, filepath)
    print("GraphML export successful!")

def compute_characterization_metrics(G):
    print("\n" + "="*60)
    print("NETWORK CHARACTERIZATION METRICS (CS 176 - STEP 2 PRELIMINARY)")
    print("="*60)

    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    density = nx.density(G)
    avg_clustering = nx.average_clustering(G)

    ccs = sorted(nx.connected_components(G), key=len, reverse=True)
    n_ccs = len(ccs)
    gcc = G.subgraph(ccs[0]).copy()
    gcc_nodes = gcc.number_of_nodes()
    gcc_edges = gcc.number_of_edges()
    gcc_pct = (gcc_nodes / n_nodes) * 100

    print(f"1. Total Number of Nodes (|V|): {n_nodes}")
    print(f"2. Total Number of Edges (|E|): {n_edges}")
    print(f"3. Connected Components: {n_ccs}")
    print(f"   - Giant Connected Component (GCC): {gcc_nodes} nodes ({gcc_pct:.1f}%), {gcc_edges} edges")
    print(f"   - Second Largest Component: {len(ccs[1]) if n_ccs > 1 else 0} nodes")
    print(f"4. Network Density: {density:.6f} (GCC Density: {nx.density(gcc):.6f})")
    print(f"5. Average Clustering Coefficient: {avg_clustering:.4f} (GCC: {nx.average_clustering(gcc):.4f})")

    # Path length and diameter on GCC
    t0 = time.time()
    diameter = nx.diameter(gcc)
    avg_path = nx.average_shortest_path_length(gcc)
    print(f"6. GCC Diameter (Longest Shortest Path): {diameter} (computed in {time.time()-t0:.2f}s)")
    print(f"7. GCC Average Shortest Path Length (Bacon Number): {avg_path:.3f}")

    # Centralities
    print("\n--- TOP-5 RANKINGS ---")
    deg_sorted = sorted(G.degree(), key=lambda x: x[1], reverse=True)[:5]
    print(f"Top 5 Nodes by Degree (Total Co-stars):")
    for rank, (act, deg) in enumerate(deg_sorted, 1):
        print(f"   {rank}. {act}: {deg} co-stars ({G.nodes[act]['film_count']} films)")

    t0 = time.time()
    bc = nx.betweenness_centrality(gcc)
    bc_sorted = sorted(bc.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"\nTop 5 Nodes by Betweenness Centrality (GCC):")
    for rank, (act, val) in enumerate(bc_sorted, 1):
        print(f"   {rank}. {act}: C_B = {val:.5f} (Degree: {G.degree(act)})")

    clust = nx.clustering(G)
    # Filter degree >= 5 to highlight meaningful dense cliques
    clust_sorted = sorted([(act, c, G.degree(act)) for act, c in clust.items() if G.degree(act) >= 5],
                          key=lambda x: (x[1], x[2]), reverse=True)[:5]
    print(f"\nTop 5 Nodes by Clustering Coefficient (degree >= 5):")
    for rank, (act, c, deg) in enumerate(clust_sorted, 1):
        print(f"   {rank}. {act}: C_i = {c:.4f} (Degree: {deg})")

    # Louvain Communities
    comms = nx_comm.louvain_communities(gcc, seed=42)
    mod_q = nx_comm.modularity(gcc, comms)
    print(f"\nLouvain Partition on GCC: {len(comms)} communities, Modularity Q = {mod_q:.4f}")

    return {
        "n_nodes": n_nodes,
        "n_edges": n_edges,
        "n_ccs": n_ccs,
        "gcc_nodes": gcc_nodes,
        "gcc_edges": gcc_edges,
        "gcc_pct": gcc_pct,
        "density": density,
        "avg_clustering": avg_clustering,
        "diameter": diameter,
        "avg_path": avg_path,
        "deg_sorted": deg_sorted,
        "bc_sorted": bc_sorted,
        "clust_sorted": clust_sorted,
        "mod_q": mod_q,
        "n_comms": len(comms)
    }

def generate_preliminary_visualization(G, output_path="/Users/joelj/Class_Stuff/176/Project/preliminary_network.png"):
    print(f"\nGenerating preliminary network visualization: {output_path}...")
    ccs = sorted(nx.connected_components(G), key=len, reverse=True)
    gcc = G.subgraph(ccs[0]).copy()

    # Detect communities for coloring
    comms = nx_comm.louvain_communities(gcc, seed=42)
    node_to_comm = {}
    for comm_id, c in enumerate(comms):
        for node in c:
            node_to_comm[node] = comm_id

    # For clear visualization, extract the 250 highest-degree core subnetwork
    core_nodes = [node for node, deg in sorted(gcc.degree(), key=lambda x: x[1], reverse=True)[:250]]
    core_subgraph = gcc.subgraph(core_nodes).copy()

    # Betweenness for sizing
    core_bc = nx.betweenness_centrality(core_subgraph)
    node_sizes = [max(40, core_bc[n] * 6000) for n in core_subgraph.nodes()]
    node_colors = [node_to_comm.get(n, 0) % 16 for n in core_subgraph.nodes()]

    plt.figure(figsize=(14, 10), dpi=300)
    pos = nx.spring_layout(core_subgraph, seed=42, k=0.18, iterations=50)

    # Draw edges
    nx.draw_networkx_edges(core_subgraph, pos, alpha=0.25, edge_color="#7f8c8d", width=0.8)

    # Draw nodes
    scatter = nx.draw_networkx_nodes(
        core_subgraph,
        pos,
        node_size=node_sizes,
        node_color=node_colors,
        cmap=plt.cm.tab20,
        alpha=0.85,
        edgecolors="#2c3e50",
        linewidths=0.5
    )

    # Label top 12 bridge actors
    top_labeled = sorted(core_bc.items(), key=lambda x: x[1], reverse=True)[:12]
    labels = {n: n for n, _ in top_labeled}
    nx.draw_networkx_labels(core_subgraph, pos, labels=labels, font_size=8, font_weight="bold", font_color="#1a1a1a")

    plt.title(
        "Modern Cinema Collaboration Network (2018–2026) — Core Topology & Structural Bridges\n"
        f"Core Subgraph: {core_subgraph.number_of_nodes()} Actors, {core_subgraph.number_of_edges()} Co-Starring Ties | Sized by Betweenness, Colored by Community",
        fontsize=12, fontweight="bold", pad=15
    )
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print("Preliminary visualization successfully generated!")

if __name__ == "__main__":
    movies = load_modern_movies()
    G = construct_collaboration_network(movies, max_billing=4)
    export_graphml(G)
    metrics = compute_characterization_metrics(G)
    generate_preliminary_visualization(G)
    print("\nAll Step 1 and preliminary Step 2/3 tasks executed successfully!")
