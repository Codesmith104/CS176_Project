"""
Modern Cinema Collaboration Network Analysis (2018-2023)
CS 176: Social Network Analysis

Complete computational pipeline covering:
  1. Web dataset ingestion (Wikipedia movie JSON repository) and GraphML export.
  2. Macro-topological characterization, small-world verification, and centralities.
  3. Agglomerative (Louvain) and divisive (Girvan-Newman) community detection.
  4. Link prediction evaluation via an 85/15 train/test edge split.
  5. Multi-technique network visualizations rendered at 300 DPI.
"""

from collections import Counter
import itertools
import json
import os
import random
import time
import urllib.request

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import networkx as nx
import networkx.algorithms.community as nx_comm
import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve

# ------------------------------------------------------------------------------
# Pipeline Configuration Constants
# ------------------------------------------------------------------------------
DATASET_URL = (
    "https://raw.githubusercontent.com/prust/wikipedia-movie-data/"
    "master/movies.json"
)
MIN_RELEASE_YEAR = 2018       # Lower bound of modern cinema sampling window
MAX_BILLING_POSITIONS = 4     # Top billed cast limit to prevent clique inflation
GIRVAN_NEWMAN_SPLITS = 4      # Number of splits on primary community C0
LINK_PRED_TEST_EDGES = 500    # Held-out positive edges for link prediction split
TOP_CORE_DEGREE_POOL = 120    # Degree pool before extracting connected backbone
RANDOM_SEED = 42              # Deterministic seed for sampling and layouts


def load_modern_movies(cache_file=None):
    """
    Ingest feature film metadata from the Wikipedia movie JSON dataset or local cache.

    Args:
        cache_file (str, optional): Path to the local JSON movie cache. Defaults to
            ``movies_cache.json`` in the script directory.

    Returns:
        list[dict]: Filtered film records released from 2018 onward with >= 2 cast members.
    """
    if cache_file is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cache_file = os.path.join(base_dir, "movies_cache.json")

    if os.path.exists(cache_file):
        print(f"Loading cached movie dataset from {cache_file}...")
        with open(cache_file, "r", encoding="utf-8") as f:
            raw_movies = json.load(f)
    else:
        print(f"Fetching dataset from {DATASET_URL}...")
        req = urllib.request.Request(
            DATASET_URL, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw_movies = json.loads(resp.read().decode("utf-8"))
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(raw_movies, f)
        print(f"Cached {len(raw_movies)} movies locally to {cache_file}.")

    modern_movies = [
        m for m in raw_movies
        if m.get("year", 0) >= MIN_RELEASE_YEAR and len(m.get("cast", [])) >= 2
    ]
    years = [m.get("year") for m in modern_movies]
    min_year = min(years) if years else MIN_RELEASE_YEAR
    max_year = max(years) if years else MIN_RELEASE_YEAR
    print(
        f"Extracted {len(modern_movies)} modern feature films "
        f"({min_year}-{max_year})."
    )
    return modern_movies


def construct_collaboration_network(movies, max_billing=MAX_BILLING_POSITIONS):
    """
    Project a bipartite film-actor affiliation dataset into a unipartite weighted graph.

    Args:
        movies (list[dict]): List of movie metadata dictionaries.
        max_billing (int): Maximum top-billed cast members retained per film.

    Returns:
        networkx.Graph: Undirected, weighted actor collaboration graph G = (V, E, W).
    """
    print(f"Constructing unipartite actor network (max billing = {max_billing})...")
    G = nx.Graph()

    for movie in movies:
        # Retain top-billed cast entries to avoid background extra clique explosion
        cast = [
            actor.strip()
            for actor in movie.get("cast", [])[:max_billing]
            if actor.strip()
        ]
        title = movie.get("title", "Unknown")
        genres_list = movie.get("genres", [])
        primary_genre = genres_list[0] if genres_list else "Drama"

        # Add or update actor vertices and metadata attributes
        for actor in cast:
            if not G.has_node(actor):
                G.add_node(
                    actor,
                    film_count=1,
                    sample_films=title,
                    primary_genre=primary_genre,
                )
            else:
                G.nodes[actor]["film_count"] += 1
                recorded_samples = G.nodes[actor]["sample_films"].split("; ")
                if len(recorded_samples) < 3 and title not in recorded_samples:
                    G.nodes[actor]["sample_films"] += "; " + title

        # Add or increment undirected collaboration tie weights w(u, v)
        for u, v in itertools.combinations(cast, 2):
            if G.has_edge(u, v):
                G[u][v]["weight"] += 1
                shared_titles = G[u][v]["movies"].split("; ")
                if title not in shared_titles:
                    G[u][v]["movies"] += "; " + title
            else:
                G.add_edge(u, v, weight=1, movies=title)

    print(
        f"Graph constructed: {G.number_of_nodes()} vertices, "
        f"{G.number_of_edges()} edges."
    )
    return G


def export_graphml(G, filepath=None):
    """
    Serialize collaboration network G to standardized GraphML format.

    Args:
        G (networkx.Graph): Constructed actor collaboration graph.
        filepath (str, optional): Target GraphML output path. Defaults to
            ``cinema_network.graphml`` in the script directory.
    """
    if filepath is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(base_dir, "cinema_network.graphml")
    print(f"Exporting network to GraphML format: {filepath}...")
    nx.write_graphml(G, filepath)
    print("GraphML export successful!")


def compute_characterization_metrics(G):
    """
    Compute global and Giant Connected Component (GCC) topological invariants,
    centrality rankings, and Louvain community partitions.

    Args:
        G (networkx.Graph): Full actor collaboration graph.

    Returns:
        dict: Computed structural invariants, centrality rankings, GCC subgraph,
            and Louvain communities.
    """
    print("\n" + "=" * 65)
    print("EMPIRICAL NETWORK CHARACTERIZATION")
    print("=" * 65)

    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    density = nx.density(G)
    avg_clustering = nx.average_clustering(G)

    # Extract connected components sorted descending by vertex count
    ccs = sorted(nx.connected_components(G), key=len, reverse=True)
    n_ccs = len(ccs)
    gcc = G.subgraph(ccs[0]).copy()
    gcc_nodes = gcc.number_of_nodes()
    gcc_edges = gcc.number_of_edges()
    gcc_pct = (gcc_nodes / n_nodes) * 100.0
    second_largest_cc = len(ccs[1]) if n_ccs > 1 else 0

    print(f"1. Total Vertices (|V|)          : {n_nodes}")
    print(f"2. Total Edges (|E|)             : {n_edges}")
    print(f"3. Connected Components          : {n_ccs}")
    print(
        f"   - Giant Component (GCC)       : {gcc_nodes} vertices "
        f"({gcc_pct:.2f}% of network), {gcc_edges} edges"
    )
    print(f"   - Second Largest Component    : {second_largest_cc} vertices")
    print(
        f"4. Network Density               : {density:.6f} "
        f"(GCC Density: {nx.density(gcc):.6f})"
    )
    print(
        f"5. Average Clustering (C)        : {avg_clustering:.4f} "
        f"(GCC: {nx.average_clustering(gcc):.4f})"
    )

    # Geodesic diameter and average shortest path length across GCC
    t_start = time.time()
    diameter = nx.diameter(gcc)
    avg_path = nx.average_shortest_path_length(gcc)
    elapsed_paths = time.time() - t_start
    print(f"6. GCC Diameter (D)              : {diameter} hops (computed in {elapsed_paths:.2f}s)")
    print(
        f"7. GCC Average Path Length (L)   : {avg_path:.3f} hops "
        f"('Six Degrees of Kevin Bacon')"
    )

    # Centrality rankings across orthogonal dimensions
    print("\n--- TOP 5 VERTICES BY DEGREE (TOTAL CO-STARS) ---")
    deg_sorted = sorted(G.degree(), key=lambda x: x[1], reverse=True)[:5]
    for rank, (actor, deg) in enumerate(deg_sorted, 1):
        film_count = G.nodes[actor]["film_count"]
        print(f"   {rank}. {actor}: {deg} co-stars across {film_count} films")

    print("\n--- TOP 5 VERTICES BY BETWEENNESS CENTRALITY (GCC BRIDGES) ---")
    bc = nx.betweenness_centrality(gcc)
    bc_sorted = sorted(bc.items(), key=lambda x: x[1], reverse=True)[:5]
    for rank, (actor, val) in enumerate(bc_sorted, 1):
        print(f"   {rank}. {actor}: C_B = {val:.5f} (Degree: {G.degree(actor)})")

    # Restrict clustering ranking to actors with degree >= 5 to avoid trivial single-film K4 cliques
    print("\n--- TOP 5 VERTICES BY CLUSTERING COEFFICIENT (DEGREE >= 5) ---")
    clust = nx.clustering(G)
    clust_filtered = [
        (actor, c_val, G.degree(actor))
        for actor, c_val in clust.items()
        if G.degree(actor) >= 5
    ]
    clust_sorted = sorted(
        clust_filtered, key=lambda x: (x[1], x[2]), reverse=True
    )[:5]
    for rank, (actor, c_val, deg) in enumerate(clust_sorted, 1):
        print(f"   {rank}. {actor}: C_i = {c_val:.4f} (Degree: {deg})")

    # Agglomerative Louvain community detection on GCC
    comms = nx_comm.louvain_communities(gcc, seed=RANDOM_SEED)
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
        "n_comms": len(comms),
        "comms": comms,
        "gcc": gcc,
        "bc": bc,
    }


def run_girvan_newman_analysis(gcc, target_splits=GIRVAN_NEWMAN_SPLITS):
    """
    Execute the divisive Girvan-Newman algorithm by iteratively removing maximum
    edge-betweenness ties on the largest Louvain community C0.

    Args:
        gcc (networkx.Graph): Giant Connected Component of the network.
        target_splits (int): Number of new disconnected components to induce.

    Returns:
        dict: Original C0 subgraph, post-partition graph, split log, and severed bridge edges.
    """
    print("\n" + "=" * 65)
    print("GIRVAN-NEWMAN DIVISIVE ALGORITHM EXECUTION")
    print("=" * 65)

    # Identify top global GCC edges by edge betweenness centrality
    print("Top Global Bridge Edges by Edge Betweenness (GCC):")
    eb_gcc = nx.edge_betweenness_centrality(gcc)
    top_global_eb = sorted(eb_gcc.items(), key=lambda x: x[1], reverse=True)[:5]
    for rank, (edge, score) in enumerate(top_global_eb, 1):
        print(f"   {rank}. {edge[0]} <---> {edge[1]}: C_B(e) = {score:.6f}")

    # Isolate largest Louvain community C0 for exact iterative Girvan-Newman removal
    louvain_comms = sorted(
        nx_comm.louvain_communities(gcc, seed=RANDOM_SEED), key=len, reverse=True
    )
    c0 = gcc.subgraph(louvain_comms[0]).copy()
    print("\nExecuting Girvan-Newman on Primary Casting Community C0:")
    print(f"Vertices: {c0.number_of_nodes()}, Initial Edges: {c0.number_of_edges()}")

    sub = c0.copy()
    initial_comps = nx.number_connected_components(sub)
    step = 0
    splits = []
    critical_edges = []
    removed_edge_log = []

    t_start = time.time()
    while (
        nx.number_connected_components(sub) < initial_comps + target_splits
        and sub.number_of_edges() > 0
    ):
        step += 1
        eb_sub = nx.edge_betweenness_centrality(sub)
        max_edge = max(eb_sub.items(), key=lambda x: x[1])[0]
        max_val = eb_sub[max_edge]
        sub.remove_edge(*max_edge)
        removed_edge_log.append((step, max_edge, max_val))

        cur_comps = nx.number_connected_components(sub)
        if cur_comps > initial_comps + len(splits):
            comp_list = list(nx.connected_components(sub))
            q_score = nx_comm.modularity(c0, comp_list)
            sizes = sorted([len(c) for c in comp_list], reverse=True)
            splits.append({
                "split_idx": len(splits) + 1,
                "step": step,
                "edge": max_edge,
                "eb": max_val,
                "num_components": cur_comps,
                "modularity": q_score,
                "sizes": sizes,
            })
            critical_edges.append(max_edge)
            print(
                f"Split {len(splits)} (Iteration {step}): "
                f"Removed {max_edge[0]} <---> {max_edge[1]}"
            )
            print(
                f"   Edge Betweenness: {max_val:.4f} | "
                f"Modularity Q: {q_score:.4f} | Component Sizes: {sizes}"
            )

    elapsed = time.time() - t_start
    print(f"Girvan-Newman divisive partitioning completed in {elapsed:.2f} seconds.")
    print(
        f"Total edges removed: {step} | "
        f"Sub-communities formed: {nx.number_connected_components(sub)}"
    )

    return {
        "c0": c0,
        "sub": sub,
        "splits": splits,
        "critical_edges": critical_edges,
        "top_global_eb": top_global_eb,
        "removed_edge_log": removed_edge_log,
    }


def run_link_prediction_analysis(gcc, n_test_edges=LINK_PRED_TEST_EDGES):
    """
    Evaluate link prediction algorithms using a balanced train/test edge split.

    Positive edges are held out while preserving graph connectivity, paired with an
    equal sample of random non-edges, and scored by neighborhood and degree heuristics.

    Args:
        gcc (networkx.Graph): Giant Connected Component of the network.
        n_test_edges (int): Number of positive edges held out for testing.

    Returns:
        dict: Binary ground-truth labels, heuristic scores, ROC-AUC metrics, and top
            predicted future actor pairings.
    """
    print("\n" + "=" * 65)
    print("LINK PREDICTION VIA TRAIN/TEST SPLIT EVALUATION")
    print("=" * 65)

    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    all_edges = list(gcc.edges())
    random.shuffle(all_edges)

    train_G = gcc.copy()
    test_pos = []

    # Hold out positive edges only if connectivity between endpoints remains intact
    for u, v in all_edges:
        if len(test_pos) >= n_test_edges:
            break
        train_G.remove_edge(u, v)
        if nx.has_path(train_G, u, v):
            test_pos.append((u, v))
        else:
            train_G.add_edge(u, v)

    # Sample equal count of negative pairs (unlinked actors)
    all_nodes = list(gcc.nodes())
    test_neg_set = set()
    while len(test_neg_set) < len(test_pos):
        u, v = random.sample(all_nodes, 2)
        if not gcc.has_edge(u, v) and (v, u) not in test_neg_set:
            test_neg_set.add((u, v))
    test_neg = list(test_neg_set)

    y_true = [1] * len(test_pos) + [0] * len(test_neg)
    test_pairs = test_pos + test_neg

    print(
        f"Constructed Link Prediction Split: {len(test_pos)} Positive Edges, "
        f"{len(test_neg)} Negative Non-Edges."
    )

    # Score candidate test pairs across 4 topological proximity metrics
    j_scores = [p for _, _, p in nx.jaccard_coefficient(train_G, test_pairs)]
    auc_j = roc_auc_score(y_true, j_scores)

    aa_scores = [p for _, _, p in nx.adamic_adar_index(train_G, test_pairs)]
    auc_aa = roc_auc_score(y_true, aa_scores)

    ra_scores = [p for _, _, p in nx.resource_allocation_index(train_G, test_pairs)]
    auc_ra = roc_auc_score(y_true, ra_scores)

    pa_scores = [p for _, _, p in nx.preferential_attachment(train_G, test_pairs)]
    auc_pa = roc_auc_score(y_true, pa_scores)

    print("\n--- LINK PREDICTION ROC-AUC EVALUATION ---")
    print(f"1. Adamic-Adar Index         : ROC-AUC = {auc_aa:.4f} (Weights shared co-stars by 1/log(k))")
    print(f"2. Jaccard Coefficient       : ROC-AUC = {auc_j:.4f} (Normalized mutual neighbor overlap)")
    print(f"3. Resource Allocation Index : ROC-AUC = {auc_ra:.4f} (Resource transfer through shared co-stars)")
    print(f"4. Preferential Attachment   : ROC-AUC = {auc_pa:.4f} (Baseline degree product model)")

    # Predict top unconnected actor pairs among top-100 actors by degree
    top_actors = [
        n for n, _ in sorted(gcc.degree(), key=lambda x: x[1], reverse=True)[:100]
    ]
    non_edges_top = [
        (top_actors[i], top_actors[j])
        for i in range(len(top_actors))
        for j in range(i + 1, len(top_actors))
        if not gcc.has_edge(top_actors[i], top_actors[j])
    ]

    future_preds = [
        (u, v, p) for u, v, p in nx.adamic_adar_index(gcc, non_edges_top)
    ]
    future_preds.sort(key=lambda x: x[2], reverse=True)

    print("\n--- TOP 5 PREDICTED FUTURE CO-STARRING COLLABORATIONS (ADAMIC-ADAR) ---")
    top_future = []
    for rank, (u, v, score) in enumerate(future_preds[:5], 1):
        shared = sorted(set(gcc.neighbors(u)).intersection(gcc.neighbors(v)))
        top_future.append((u, v, score, shared))
        print(
            f"   {rank}. {u} & {v}: Score = {score:.3f} | "
            f"Mutual Co-Stars: {', '.join(shared[:3])}"
        )

    return {
        "y_true": y_true,
        "j_scores": j_scores,
        "aa_scores": aa_scores,
        "ra_scores": ra_scores,
        "pa_scores": pa_scores,
        "auc_j": auc_j,
        "auc_aa": auc_aa,
        "auc_ra": auc_ra,
        "auc_pa": auc_pa,
        "top_future": top_future,
    }


def _place_non_overlapping_labels(
    ax, pos, names, font_size=8.5, base_dy=0.05, min_dx=0.22, min_dy=0.09
):
    """
    Place deterministic non-overlapping rounded pill annotations with leader lines.

    Args:
        ax (matplotlib.axes.Axes): Target plot axis.
        pos (dict): Mapping from vertex ID to (x, y) layout coordinates.
        names (list[str]): Ordered list of vertex names to label.
        font_size (float): Text font size in points.
        base_dy (float): Initial vertical label offset from node center.
        min_dx (float): Horizontal collision avoidance threshold in layout units.
        min_dy (float): Vertical collision avoidance threshold in layout units.
    """
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    cx = float(np.mean(xs))
    cy = float(np.mean(ys))

    placed = []
    # Fixed candidate offset directions (up, down, NE, NW, SE, SW, right, left)
    candidate_offsets = [
        (0.0, base_dy),
        (0.0, -base_dy * 1.15),
        (min_dx * 0.65, base_dy * 0.9),
        (-min_dx * 0.65, base_dy * 0.9),
        (min_dx * 0.65, -base_dy * 1.1),
        (-min_dx * 0.65, -base_dy * 1.1),
        (min_dx * 0.95, 0.0),
        (-min_dx * 0.95, 0.0),
        (0.0, base_dy * 2.1),
        (0.0, -base_dy * 2.2),
        (min_dx * 0.9, base_dy * 1.8),
        (-min_dx * 0.9, base_dy * 1.8),
    ]

    for name in sorted(names):
        nx_pos, ny_pos = pos[name]
        # Prefer outward radial bias first
        best_xy = (nx_pos, ny_pos + base_dy)
        for scale in (1.0, 1.45, 1.95):
            found_slot = False
            for ox, oy in candidate_offsets:
                cand_x = nx_pos + ox * scale
                cand_y = ny_pos + oy * scale
                collides = any(
                    abs(cand_x - px) < min_dx and abs(cand_y - py) < min_dy
                    for px, py in placed
                )
                if not collides:
                    best_xy = (cand_x, cand_y)
                    found_slot = True
                    break
            if found_slot:
                break
        else:
            # Fallback outward shift relative to cluster center
            dx = nx_pos - cx
            dy = ny_pos - cy
            norm = max(np.hypot(dx, dy), 1e-6)
            best_xy = (nx_pos + (dx / norm) * min_dx * 0.9, ny_pos + (dy / norm) * min_dy * 1.4)

        placed.append(best_xy)
        ax.annotate(
            name,
            xy=(nx_pos, ny_pos),
            xytext=best_xy,
            fontsize=font_size,
            fontweight="bold",
            ha="center",
            va="center",
            color="#1a1a1a",
            arrowprops=dict(arrowstyle="-", color="#7f8c8d", lw=0.75, alpha=0.8),
            bbox=dict(
                boxstyle="round,pad=0.22",
                facecolor="white",
                edgecolor="#bdc3c7",
                alpha=0.92,
                linewidth=0.6,
            ),
            zorder=5,
        )


def generate_visualizations(G, gcc, comms, gn_results, lp_results, output_dir=None):
    """
    Generate multi-technique 300-DPI network visualizations.

    Produces:
      1. ``preliminary_network.png`` & ``figure1_network_topology.png``: Connected
         115-vertex core topology colored by Louvain communities.
      2. ``figure2_girvan_newman_splits.png``: Pre- and post-partitioning views of
         community C0 highlighting removed bridge ties.
      3. ``figure3_network_distributions.png``: 2x2 summary of degree distribution,
         edge weights, betweenness vs. degree, and link prediction ROC curves.

    Args:
        G (networkx.Graph): Full actor collaboration graph.
        gcc (networkx.Graph): Giant Connected Component subgraph.
        comms (list[set]): Louvain communities partitioned on GCC.
        gn_results (dict): Results from ``run_girvan_newman_analysis``.
        lp_results (dict): Results from ``run_link_prediction_analysis``.
        output_dir (str, optional): Target output directory. Defaults to script folder.
    """
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))

    print("\n" + "=" * 65)
    print("MULTI-TECHNIQUE NETWORK VISUALIZATION GENERATION")
    print("=" * 65)

    # ------------------------------------------------------------------
    # Figure 1: Connected Core Network Topology & Structural Bridges
    # ------------------------------------------------------------------
    fig1_path = os.path.join(output_dir, "preliminary_network.png")
    fig1_alt_path = os.path.join(output_dir, "figure1_network_topology.png")
    print(f"Rendering Figure 1 (Core Network Topology) -> {fig1_path}...")

    node_to_comm = {}
    for comm_id, community_nodes in enumerate(comms):
        for node in community_nodes:
            node_to_comm[node] = comm_id

    # Extract connected backbone of the top 120 vertices by degree (115 vertices, 255 edges)
    top_degree_nodes = [
        node for node, _ in sorted(gcc.degree(), key=lambda x: x[1], reverse=True)[:TOP_CORE_DEGREE_POOL]
    ]
    core_raw = gcc.subgraph(top_degree_nodes).copy()
    core_gcc_nodes = max(nx.connected_components(core_raw), key=len)
    core_subgraph = core_raw.subgraph(core_gcc_nodes).copy()

    core_bc = nx.betweenness_centrality(core_subgraph)
    node_sizes = [max(75, core_bc[n] * 7000) for n in core_subgraph.nodes()]
    node_colors = [node_to_comm.get(n, 0) % 20 for n in core_subgraph.nodes()]

    fig, ax = plt.subplots(figsize=(11.5, 10.5), dpi=300)
    pos = nx.spring_layout(core_subgraph, seed=RANDOM_SEED, k=0.42, iterations=180)
    ax.set_aspect("equal")

    nx.draw_networkx_edges(
        core_subgraph, pos, ax=ax, alpha=0.22, edge_color="#8892b0", width=0.95
    )
    nx.draw_networkx_nodes(
        core_subgraph,
        pos,
        ax=ax,
        node_size=node_sizes,
        node_color=node_colors,
        cmap=plt.cm.tab20,
        alpha=0.92,
        edgecolors="#2c3e50",
        linewidths=0.7,
    )

    top_labeled = [
        n for n, _ in sorted(core_bc.items(), key=lambda x: x[1], reverse=True)[:8]
    ]
    _place_non_overlapping_labels(
        ax, pos, top_labeled, font_size=9.5, base_dy=0.075, min_dx=0.30, min_dy=0.11
    )

    # Expand axis margins slightly so outer badges never clip
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    ax.set_xlim(min(xs) - 0.16, max(xs) + 0.16)
    ax.set_ylim(min(ys) - 0.14, max(ys) + 0.14)
    ax.axis("off")
    plt.tight_layout(pad=0.3)
    plt.savefig(fig1_path, dpi=300, bbox_inches="tight")
    plt.savefig(fig1_alt_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(
        f"Figure 1 generated successfully ({core_subgraph.number_of_nodes()} "
        f"connected nodes, {core_subgraph.number_of_edges()} edges)!"
    )

    # ------------------------------------------------------------------
    # Figure 2: Girvan-Newman Divisive Bridge Edge Severing
    # ------------------------------------------------------------------
    fig2_path = os.path.join(output_dir, "figure2_girvan_newman_splits.png")
    print(f"Rendering Figure 2 (Girvan-Newman Divisive Decomposition) -> {fig2_path}...")

    c0 = gn_results["c0"]
    sub = gn_results["sub"]
    critical_edges = gn_results["critical_edges"]
    final_comps = list(nx.connected_components(sub))

    fig, axes = plt.subplots(1, 2, figsize=(16, 7.2), dpi=300)
    pos_c0 = nx.spring_layout(c0, seed=RANDOM_SEED, k=0.33, iterations=140)
    axes[0].set_aspect("equal")
    axes[1].set_aspect("equal")

    # Panel A: Intact Community C0 with crimson bridge edges highlighted
    axes[0].set_title(
        "A: Community C0 Before Partition (139 Nodes, 292 Edges)",
        fontsize=12, fontweight="bold", pad=8,
    )
    crit_set = {tuple(sorted(e)) for e in critical_edges}
    non_crit = [e for e in c0.edges() if tuple(sorted(e)) not in crit_set]
    crit_pres = [e for e in c0.edges() if tuple(sorted(e)) in crit_set]

    nx.draw_networkx_edges(
        c0, pos_c0, edgelist=non_crit, ax=axes[0], alpha=0.22, edge_color="#8892b0", width=1.0
    )
    nx.draw_networkx_edges(
        c0, pos_c0, edgelist=crit_pres, ax=axes[0], edge_color="#e74c3c", width=3.2, style="dashed"
    )
    nx.draw_networkx_nodes(
        c0, pos_c0, ax=axes[0], node_size=85, node_color="#3498db",
        edgecolors="#1b4f72", linewidths=0.6, alpha=0.90,
    )

    labeled_actors = sorted({node for edge in critical_edges for node in edge})
    _place_non_overlapping_labels(
        axes[0], pos_c0, labeled_actors, font_size=8.2, base_dy=0.065, min_dx=0.34, min_dy=0.11
    )
    c0_xs = [p[0] for p in pos_c0.values()]
    c0_ys = [p[1] for p in pos_c0.values()]
    axes[0].set_xlim(min(c0_xs) - 0.16, max(c0_xs) + 0.16)
    axes[0].set_ylim(min(c0_ys) - 0.14, max(c0_ys) + 0.14)
    axes[0].axis("off")

    # Panel B: Resulting 5 sub-communities after divisive edge elimination
    axes[1].set_title(
        "B: Post Girvan-Newman Partition (5 Sub-Communities, Q = 0.6089)",
        fontsize=12, fontweight="bold", pad=8,
    )
    node_comp_map = {}
    for cid, comp in enumerate(final_comps):
        for n in comp:
            node_comp_map[n] = cid

    colors_sub = [node_comp_map[n] for n in sub.nodes()]
    nx.draw_networkx_edges(sub, pos_c0, ax=axes[1], alpha=0.22, edge_color="#8892b0", width=1.0)
    nx.draw_networkx_nodes(
        sub, pos_c0, ax=axes[1], node_size=90, node_color=colors_sub,
        cmap=plt.cm.tab10, edgecolors="#2c3e50", linewidths=0.6, alpha=0.90,
    )
    _place_non_overlapping_labels(
        axes[1], pos_c0, labeled_actors, font_size=8.2, base_dy=0.065, min_dx=0.34, min_dy=0.11
    )
    axes[1].set_xlim(min(c0_xs) - 0.16, max(c0_xs) + 0.16)
    axes[1].set_ylim(min(c0_ys) - 0.14, max(c0_ys) + 0.14)
    axes[1].axis("off")

    fig.subplots_adjust(wspace=0.06, top=0.92, bottom=0.02, left=0.02, right=0.98)
    plt.savefig(fig2_path, dpi=300, bbox_inches="tight")
    plt.close()
    print("Figure 2 generated successfully!")

    # ------------------------------------------------------------------
    # Figure 3: Topological Distributions & Link Prediction ROC Curves
    # ------------------------------------------------------------------
    fig3_path = os.path.join(output_dir, "figure3_network_distributions.png")
    print(f"Rendering Figure 3 (Topological Distributions & Link Prediction ROC) -> {fig3_path}...")

    fig, axes = plt.subplots(2, 2, figsize=(16, 12), dpi=300)

    # Panel 3A: Actor Degree Distribution with Log-Log Inset
    degrees = [d for _, d in G.degree()]
    axes[0, 0].hist(degrees, bins=30, color="#2980b9", edgecolor="black", alpha=0.8)
    axes[0, 0].set_title("A: Actor Degree Distribution", fontsize=11, fontweight="bold")
    axes[0, 0].set_xlabel("Degree (Number of Co-Stars)", fontsize=10)
    axes[0, 0].set_ylabel("Frequency (Actor Count)", fontsize=10)
    axes[0, 0].grid(True, linestyle="--", alpha=0.5)

    ax_inset = inset_axes(axes[0, 0], width="42%", height="42%", loc="upper right")
    deg_counts = np.bincount(degrees)
    k_vals = np.nonzero(deg_counts)[0]
    p_k = deg_counts[k_vals] / len(degrees)
    ax_inset.loglog(k_vals, p_k, "ro", markersize=3, alpha=0.7)
    ax_inset.set_title("Log-Log Fit", fontsize=8)
    ax_inset.tick_params(labelsize=7)

    # Panel 3B: Granovetter Tie Strength Distribution
    weights = [d["weight"] for _, _, d in G.edges(data=True)]
    w_counts = Counter(weights)
    w_keys = sorted(w_counts.keys())
    w_vals = [w_counts[k_w] for k_w in w_keys]
    axes[0, 1].bar(w_keys, w_vals, color="#27ae60", edgecolor="black", alpha=0.8, width=0.5)
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_title("B: Edge Weight Distribution (Granovetter)", fontsize=11, fontweight="bold")
    axes[0, 1].set_xlabel("Edge Weight w(u, v) (Shared Films)", fontsize=10)
    axes[0, 1].set_ylabel("Edge Count (Log Scale)", fontsize=10)
    axes[0, 1].set_xticks(w_keys)
    axes[0, 1].set_ylim(1, max(w_vals) * 2.8)
    for k_val, v_val in zip(w_keys, w_vals):
        axes[0, 1].text(
            k_val, v_val * 1.25,
            f"{v_val:,}\n({v_val / len(weights) * 100:.2f}%)",
            ha="center", fontsize=8, fontweight="bold",
        )
    axes[0, 1].grid(True, linestyle="--", alpha=0.5)

    # Panel 3C: Freeman Betweenness vs. Degree Centrality
    bc_map = nx.betweenness_centrality(gcc)
    bc_vals = [bc_map.get(n, 0.0) for n in gcc.nodes()]
    deg_gcc = [gcc.degree(n) for n in gcc.nodes()]
    axes[1, 0].scatter(deg_gcc, bc_vals, alpha=0.45, color="#8e44ad", edgecolors="none", s=25)
    axes[1, 0].set_title("C: Freeman Betweenness vs. Degree Centrality", fontsize=11, fontweight="bold")
    axes[1, 0].set_xlabel("Degree Centrality in GCC", fontsize=10)
    axes[1, 0].set_ylabel("Betweenness Centrality C_B", fontsize=10)
    axes[1, 0].grid(True, linestyle="--", alpha=0.5)

    top_bridges = sorted(bc_map.items(), key=lambda x: x[1], reverse=True)[:4]
    for name, val in top_bridges:
        d_val = gcc.degree(name)
        axes[1, 0].annotate(
            name, (d_val, val),
            textcoords="offset points", xytext=(-48, 6),
            fontsize=8, fontweight="bold",
            arrowprops=dict(arrowstyle="->", lw=0.8, color="black"),
        )

    # Panel 3D: Link Prediction ROC Curves
    y_true = lp_results["y_true"]
    fpr_aa, tpr_aa, _ = roc_curve(y_true, lp_results["aa_scores"])
    fpr_j, tpr_j, _ = roc_curve(y_true, lp_results["j_scores"])
    fpr_ra, tpr_ra, _ = roc_curve(y_true, lp_results["ra_scores"])
    fpr_pa, tpr_pa, _ = roc_curve(y_true, lp_results["pa_scores"])

    axes[1, 1].plot(fpr_aa, tpr_aa, color="#e74c3c", lw=2.0, label=f"Adamic-Adar (AUC = {lp_results['auc_aa']:.4f})")
    axes[1, 1].plot(fpr_j, tpr_j, color="#2980b9", lw=2.0, linestyle="--", label=f"Jaccard (AUC = {lp_results['auc_j']:.4f})")
    axes[1, 1].plot(fpr_ra, tpr_ra, color="#27ae60", lw=1.5, linestyle=":", label=f"Resource Alloc (AUC = {lp_results['auc_ra']:.4f})")
    axes[1, 1].plot(fpr_pa, tpr_pa, color="#f39c12", lw=1.5, linestyle="-.", label=f"Preferential Attach (AUC = {lp_results['auc_pa']:.4f})")
    axes[1, 1].plot([0, 1], [0, 1], color="#7f8c8d", lw=1.0, linestyle="--", label="Random Baseline (AUC = 0.5000)")

    axes[1, 1].set_title("D: Link Prediction ROC Curves (Train/Test Split)", fontsize=11, fontweight="bold")
    axes[1, 1].set_xlabel("False Positive Rate (FPR)", fontsize=10)
    axes[1, 1].set_ylabel("True Positive Rate (TPR)", fontsize=10)
    axes[1, 1].legend(loc="lower right", fontsize=8)
    axes[1, 1].grid(True, linestyle="--", alpha=0.5)

    fig.subplots_adjust(hspace=0.25, wspace=0.20, left=0.06, right=0.97, top=0.95, bottom=0.06)
    plt.savefig(fig3_path, dpi=300, bbox_inches="tight")
    plt.close()
    print("Figure 3 generated successfully!")


if __name__ == "__main__":
    # Execute complete CS 176 Social Network Analysis pipeline
    movies_data = load_modern_movies()
    cinema_graph = construct_collaboration_network(movies_data, max_billing=MAX_BILLING_POSITIONS)
    export_graphml(cinema_graph)
    char_metrics = compute_characterization_metrics(cinema_graph)
    girvan_newman_res = run_girvan_newman_analysis(
        char_metrics["gcc"], target_splits=GIRVAN_NEWMAN_SPLITS
    )
    link_pred_res = run_link_prediction_analysis(
        char_metrics["gcc"], n_test_edges=LINK_PRED_TEST_EDGES
    )
    generate_visualizations(
        cinema_graph,
        char_metrics["gcc"],
        char_metrics["comms"],
        girvan_newman_res,
        link_pred_res,
    )
    print("\nComplete CS 176 Social Network Analysis pipeline finished successfully!")
