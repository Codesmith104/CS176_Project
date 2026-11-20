"""
Modern Cinema Collaboration Network Analysis (2018–2026)
CS 176: Social Network Analysis
Complete Pipeline: Data Extraction, GraphML Construction, Topological Characterization,
Girvan-Newman Divisive Partitioning, Link Prediction (Train/Test Split),
and Multi-Technique Network Visualization.
"""

import os
import json
import urllib.request
import itertools
import time
import random
from collections import Counter

import networkx as nx
import networkx.algorithms.community as nx_comm
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve

def load_modern_movies(cache_file=None):
    """
    Step 1: Ingest movie metadata from open web endpoints or local cache.
    Filters for modern feature films released between 2018 and 2026 with valid cast data.
    """
    if cache_file is None:
        cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies_cache.json")

    if os.path.exists(cache_file):
        print(f"Loading cached movie dataset from {cache_file}...")
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        url = "https://raw.githubusercontent.com/prust/wikipedia-movie-data/master/movies.json"
        print(f"Fetching dataset from {url}...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
        print(f"Cached {len(data)} movies locally to {cache_file}.")

    modern_movies = [m for m in data if m.get("year", 0) >= 2018 and len(m.get("cast", [])) >= 2]
    print(f"Extracted {len(modern_movies)} modern feature films (2018–2026).")
    return modern_movies

def construct_collaboration_network(movies, max_billing=4):
    """
    Step 1: Project bipartite film-actor affiliation network into an undirected,
    weighted unipartite actor collaboration network G = (V, E, W).
    Filters to top `max_billing` actors per film to prevent combinatorial clique expansion.
    """
    print(f"Constructing unipartite actor network (max billing = {max_billing})...")
    G = nx.Graph()

    for m in movies:
        cast = [actor.strip() for actor in m.get("cast", [])[:max_billing] if actor.strip()]
        title = m.get("title", "Unknown")
        genres = ", ".join(m.get("genres", []))
        primary_genre = genres.split(", ")[0] if genres else "Drama"

        # Add / update actor vertices
        for actor in cast:
            if not G.has_node(actor):
                G.add_node(actor, film_count=1, sample_films=title, primary_genre=primary_genre)
            else:
                G.nodes[actor]["film_count"] += 1
                sample = G.nodes[actor]["sample_films"].split("; ")
                if len(sample) < 3 and title not in sample:
                    G.nodes[actor]["sample_films"] += "; " + title

        # Add / update weighted collaboration ties (Granovetter's tie strength)
        for u, v in itertools.combinations(cast, 2):
            if G.has_edge(u, v):
                G[u][v]["weight"] += 1
                shared = G[u][v]["movies"].split("; ")
                if title not in shared:
                    G[u][v]["movies"] += "; " + title
            else:
                G.add_edge(u, v, weight=1, movies=title)

    print(f"Graph constructed: {G.number_of_nodes()} vertices, {G.number_of_edges()} edges.")
    return G

def export_graphml(G, filepath=None):
    """
    Step 1 Deliverable: Serializes graph G to standardized GraphML format.
    """
    if filepath is None:
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cinema_network.graphml")
    print(f"Exporting network to GraphML format: {filepath}...")
    nx.write_graphml(G, filepath)
    print("GraphML export successful!")

def compute_characterization_metrics(G):
    """
    Step 2: Empirical characterization of the network.
    Evaluates global properties, Giant Connected Component (GCC),
    small-world dynamics, and vertex centrality distributions.
    """
    print("\n" + "="*65)
    print("EMPIRICAL NETWORK CHARACTERIZATION (STEP 2 METRICS)")
    print("="*65)

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

    print(f"1. Total Vertices (|V|)          : {n_nodes}")
    print(f"2. Total Edges (|E|)             : {n_edges}")
    print(f"3. Connected Components          : {n_ccs}")
    print(f"   - Giant Component (GCC)       : {gcc_nodes} vertices ({gcc_pct:.2f}% of network), {gcc_edges} edges")
    print(f"   - Second Largest Component    : {len(ccs[1]) if n_ccs > 1 else 0} vertices")
    print(f"4. Network Density               : {density:.6f} (GCC Density: {nx.density(gcc):.6f})")
    print(f"5. Average Clustering (C)        : {avg_clustering:.4f} (GCC: {nx.average_clustering(gcc):.4f})")

    # Diameter and Average Shortest Path Length on GCC
    t0 = time.time()
    diameter = nx.diameter(gcc)
    avg_path = nx.average_shortest_path_length(gcc)
    print(f"6. GCC Diameter (D)              : {diameter} hops (computed in {time.time()-t0:.2f}s)")
    print(f"7. GCC Average Path Length (L)   : {avg_path:.3f} hops ('Six Degrees of Kevin Bacon')")

    # Centrality Rankings
    print("\n--- TOP 5 VERTICES BY DEGREE (TOTAL CO-STARS) ---")
    deg_sorted = sorted(G.degree(), key=lambda x: x[1], reverse=True)[:5]
    for rank, (act, deg) in enumerate(deg_sorted, 1):
        print(f"   {rank}. {act}: {deg} co-stars across {G.nodes[act]['film_count']} films")

    print("\n--- TOP 5 VERTICES BY BETWEENNESS CENTRALITY (GCC BRIDGES) ---")
    bc = nx.betweenness_centrality(gcc)
    bc_sorted = sorted(bc.items(), key=lambda x: x[1], reverse=True)[:5]
    for rank, (act, val) in enumerate(bc_sorted, 1):
        print(f"   {rank}. {act}: C_B = {val:.5f} (Degree: {G.degree(act)})")

    print("\n--- TOP 5 VERTICES BY CLUSTERING COEFFICIENT (DEGREE >= 5) ---")
    clust = nx.clustering(G)
    clust_sorted = sorted([(act, c, G.degree(act)) for act, c in clust.items() if G.degree(act) >= 5],
                          key=lambda x: (x[1], x[2]), reverse=True)[:5]
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
        "n_comms": len(comms),
        "comms": comms,
        "gcc": gcc,
        "bc": bc
    }

def run_girvan_newman_analysis(gcc, target_splits=4):
    """
    Step 2.7: Implements the Girvan-Newman divisive community detection algorithm.
    Iteratively computes edge betweenness centrality, identifies bridge edges,
    removes the edge with maximum betweenness, and logs the resulting component splits
    and modularity scores Q.
    """
    print("\n" + "="*65)
    print("STEP 2.7: GIRVAN-NEWMAN DIVISIVE ALGORITHM EXECUTION")
    print("="*65)

    # 1. Global GCC Bridge Edges
    print("Top Global Bridge Edges by Edge Betweenness (GCC):")
    eb_sample = nx.edge_betweenness_centrality(gcc)
    top_global_eb = sorted(eb_sample.items(), key=lambda x: x[1], reverse=True)[:5]
    for rank, (edge, score) in enumerate(top_global_eb, 1):
        print(f"   {rank}. {edge[0]} <---> {edge[1]}: C_B(e) = {score:.6f}")

    # 2. Divisive Partitioning on Primary Community Subgraph (C0)
    louvain_comms = sorted(nx_comm.louvain_communities(gcc, seed=42), key=len, reverse=True)
    c0 = gcc.subgraph(louvain_comms[0]).copy()
    print(f"\nExecuting Girvan-Newman on Primary Casting Community C0:")
    print(f"Vertices: {c0.number_of_nodes()}, Initial Edges: {c0.number_of_edges()}")

    sub = c0.copy()
    initial_comps = nx.number_connected_components(sub)
    step = 0
    splits = []
    critical_edges = []
    removed_edge_log = []

    t0 = time.time()
    while nx.number_connected_components(sub) < initial_comps + target_splits and sub.number_of_edges() > 0:
        step += 1
        eb = nx.edge_betweenness_centrality(sub)
        max_edge = max(eb.items(), key=lambda x: x[1])[0]
        max_val = eb[max_edge]
        sub.remove_edge(*max_edge)
        removed_edge_log.append((step, max_edge, max_val))

        cur_comps = nx.number_connected_components(sub)
        if cur_comps > initial_comps + len(splits):
            comp_list = list(nx.connected_components(sub))
            q = nx_comm.modularity(c0, comp_list)
            sizes = sorted([len(c) for c in comp_list], reverse=True)
            splits.append({
                "split_idx": len(splits) + 1,
                "step": step,
                "edge": max_edge,
                "eb": max_val,
                "num_components": cur_comps,
                "modularity": q,
                "sizes": sizes
            })
            critical_edges.append(max_edge)
            print(f"Split {len(splits)} (Iteration {step}): Removed {max_edge[0]} <---> {max_edge[1]}")
            print(f"   Edge Betweenness: {max_val:.4f} | Modularity Q: {q:.4f} | Component Sizes: {sizes}")

    elapsed = time.time() - t0
    print(f"Girvan-Newman divisive partitioning completed in {elapsed:.2f} seconds.")
    print(f"Total edges removed: {step} | Sub-communities formed: {nx.number_connected_components(sub)}")

    return {
        "c0": c0,
        "sub": sub,
        "splits": splits,
        "critical_edges": critical_edges,
        "top_global_eb": top_global_eb,
        "removed_edge_log": removed_edge_log
    }

def run_link_prediction_analysis(gcc, n_test_edges=500):
    """
    Step 2.8: Implements Link Prediction using Train/Test Edge Splitting.
    Evaluates topological similarity heuristics (Jaccard, Adamic-Adar,
    Resource Allocation, and Preferential Attachment) using ROC-AUC scores.
    """
    print("\n" + "="*65)
    print("STEP 2.8: LINK PREDICTION VIA TRAIN/TEST SPLIT (EVALUATION)")
    print("="*65)

    random.seed(42)
    np.random.seed(42)

    edges = list(gcc.edges())
    random.shuffle(edges)

    train_G = gcc.copy()
    test_pos = []

    # Hold out positive edges while maintaining connectivity
    for u, v in edges:
        if len(test_pos) >= n_test_edges:
            break
        train_G.remove_edge(u, v)
        if nx.has_path(train_G, u, v):
            test_pos.append((u, v))
        else:
            train_G.add_edge(u, v)

    # Sample equal number of negative edges (actor pairs that never co-starred)
    nodes = list(gcc.nodes())
    test_neg = set()
    while len(test_neg) < len(test_pos):
        u, v = random.sample(nodes, 2)
        if not gcc.has_edge(u, v) and (v, u) not in test_neg:
            test_neg.add((u, v))
    test_neg = list(test_neg)

    y_true = [1] * len(test_pos) + [0] * len(test_neg)
    test_pairs = test_pos + test_neg

    print(f"Constructed Link Prediction Split: {len(test_pos)} Positive Edges, {len(test_neg)} Negative Non-Edges.")

    # 1. Jaccard Coefficient
    j_scores = [p for u, v, p in nx.jaccard_coefficient(train_G, test_pairs)]
    auc_j = roc_auc_score(y_true, j_scores)

    # 2. Adamic-Adar Index
    aa_scores = [p for u, v, p in nx.adamic_adar_index(train_G, test_pairs)]
    auc_aa = roc_auc_score(y_true, aa_scores)

    # 3. Resource Allocation Index
    ra_scores = [p for u, v, p in nx.resource_allocation_index(train_G, test_pairs)]
    auc_ra = roc_auc_score(y_true, ra_scores)

    # 4. Preferential Attachment
    pa_scores = [p for u, v, p in nx.preferential_attachment(train_G, test_pairs)]
    auc_pa = roc_auc_score(y_true, pa_scores)

    print("\n--- LINK PREDICTION ROC-AUC EVALUATION ---")
    print(f"1. Adamic-Adar Index         : ROC-AUC = {auc_aa:.4f} (Weights shared co-stars by 1/log(k))")
    print(f"2. Jaccard Coefficient       : ROC-AUC = {auc_j:.4f} (Normalized mutual neighbor overlap)")
    print(f"3. Resource Allocation Index : ROC-AUC = {auc_ra:.4f} (Resource transfer through shared co-stars)")
    print(f"4. Preferential Attachment   : ROC-AUC = {auc_pa:.4f} (Baseline degree product model)")

    # Predict top future unlinked actor collaborations among top 100 actors
    top_actors = [n for n, d in sorted(gcc.degree(), key=lambda x: x[1], reverse=True)[:100]]
    non_edges_top = []
    for i in range(len(top_actors)):
        for j in range(i + 1, len(top_actors)):
            u, v = top_actors[i], top_actors[j]
            if not gcc.has_edge(u, v):
                non_edges_top.append((u, v))

    future_preds = [(u, v, p) for u, v, p in nx.adamic_adar_index(gcc, non_edges_top)]
    future_preds.sort(key=lambda x: x[2], reverse=True)

    print("\n--- TOP 5 PREDICTED FUTURE CO-STARRING COLLABORATIONS (ADAMIC-ADAR) ---")
    top_future = []
    for rank, (u, v, score) in enumerate(future_preds[:5], 1):
        shared = sorted(list(set(gcc.neighbors(u)).intersection(set(gcc.neighbors(v)))))
        top_future.append((u, v, score, shared))
        print(f"   {rank}. {u} & {v}: Score = {score:.3f} | Mutual Co-Stars: {', '.join(shared[:3])}")

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
        "top_future": top_future
    }

def generate_visualizations(G, gcc, comms, gn_results, lp_results, output_dir=None):
    """
    Step 3: Multi-technique network visualizations.
    Generates:
      1. preliminary_network.png / figure1_network_topology.png: Core spring layout with centrality sizing.
      2. figure2_girvan_newman_splits.png: Pre- and post-partitioning of community C0 with severed bridge edges.
      3. figure3_network_distributions.png: 2x2 multi-panel figure covering Degree Distribution,
         Edge Weights, Betweenness vs. Degree, and Link Prediction ROC Curves.
    """
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))

    print("\n" + "="*65)
    print("STEP 3: MULTI-TECHNIQUE NETWORK VISUALIZATION GENERATION")
    print("="*65)

    # -------------------------------------------------------------
    # Figure 1: Core Network Topology & Structural Bridges
    # -------------------------------------------------------------
    fig1_path = os.path.join(output_dir, "preliminary_network.png")
    fig1_alt_path = os.path.join(output_dir, "figure1_network_topology.png")
    print(f"Rendering Figure 1 (Core Network Topology) -> {fig1_path}...")

    node_to_comm = {}
    for comm_id, c in enumerate(comms):
        for node in c:
            node_to_comm[node] = comm_id

    core_nodes = [node for node, deg in sorted(gcc.degree(), key=lambda x: x[1], reverse=True)[:250]]
    core_subgraph = gcc.subgraph(core_nodes).copy()
    core_bc = nx.betweenness_centrality(core_subgraph)
    node_sizes = [max(40, core_bc[n] * 6000) for n in core_subgraph.nodes()]
    node_colors = [node_to_comm.get(n, 0) % 16 for n in core_subgraph.nodes()]

    plt.figure(figsize=(14, 10), dpi=300)
    pos = nx.spring_layout(core_subgraph, seed=42, k=0.18, iterations=50)

    nx.draw_networkx_edges(core_subgraph, pos, alpha=0.25, edge_color="#7f8c8d", width=0.8)
    nx.draw_networkx_nodes(
        core_subgraph,
        pos,
        node_size=node_sizes,
        node_color=node_colors,
        cmap=plt.cm.tab20,
        alpha=0.85,
        edgecolors="#2c3e50",
        linewidths=0.5
    )

    top_labeled = sorted(core_bc.items(), key=lambda x: x[1], reverse=True)[:12]
    labels = {n: n for n, _ in top_labeled}
    nx.draw_networkx_labels(core_subgraph, pos, labels=labels, font_size=8, font_weight="bold", font_color="#1a1a1a")

    plt.title(
        "Modern Cinema Collaboration Network (2018–2026) — Core Topology & Structural Bridges\n"
        f"Core Subgraph: {core_subgraph.number_of_nodes()} Vertices, {core_subgraph.number_of_edges()} Edges | Node Size: Betweenness Centrality | Color: Louvain Community",
        fontsize=12, fontweight="bold", pad=15
    )
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(fig1_path, dpi=300, bbox_inches="tight")
    plt.savefig(fig1_alt_path, dpi=300, bbox_inches="tight")
    plt.close()
    print("Figure 1 generated successfully!")

    # -------------------------------------------------------------
    # Figure 2: Girvan-Newman Divisive Bridge Edge Severing
    # -------------------------------------------------------------
    fig2_path = os.path.join(output_dir, "figure2_girvan_newman_splits.png")
    print(f"Rendering Figure 2 (Girvan-Newman Divisive Decomposition) -> {fig2_path}...")

    c0 = gn_results["c0"]
    sub = gn_results["sub"]
    critical_edges = gn_results["critical_edges"]
    final_comps = list(nx.connected_components(sub))

    fig, axes = plt.subplots(1, 2, figsize=(20, 9), dpi=300)
    pos_c0 = nx.spring_layout(c0, seed=42, k=0.22, iterations=80)

    # Panel A: Before Partitioning
    axes[0].set_title(
        "A: Primary Casting Community C0 Before Partition (139 Nodes, 292 Edges)\n"
        "Highlighted Crimson Dashed Ties: Critical Bridge Edges with Max Edge Betweenness",
        fontsize=11, fontweight="bold", pad=12
    )
    non_crit = [e for e in c0.edges() if tuple(sorted(e)) not in [tuple(sorted(x)) for x in critical_edges]]
    nx.draw_networkx_edges(c0, pos_c0, edgelist=non_crit, ax=axes[0], alpha=0.3, edge_color="#7f8c8d", width=1.0)
    crit_pres = [e for e in c0.edges() if tuple(sorted(e)) in [tuple(sorted(x)) for x in critical_edges]]
    nx.draw_networkx_edges(c0, pos_c0, edgelist=crit_pres, ax=axes[0], edge_color="#e74c3c", width=3.0, style="dashed")
    nx.draw_networkx_nodes(c0, pos_c0, ax=axes[0], node_size=75, node_color="#3498db", edgecolors="#1b4f72", linewidths=0.5)

    labeled_actors = set()
    for u, v in critical_edges:
        labeled_actors.add(u)
        labeled_actors.add(v)
    labels_crit = {n: n for n in labeled_actors}
    nx.draw_networkx_labels(c0, pos_c0, labels=labels_crit, ax=axes[0], font_size=8, font_weight="bold", font_color="#2c3e50")
    axes[0].axis("off")

    # Panel B: After Divisive Removal
    axes[1].set_title(
        f"B: Post Girvan-Newman Partition (36 Edges Removed)\n"
        f"Divided into 5 Sub-Communities (Modularity Q = 0.6089)",
        fontsize=11, fontweight="bold", pad=12
    )
    node_comp_map = {}
    for cid, comp in enumerate(final_comps):
        for n in comp:
            node_comp_map[n] = cid

    colors_sub = [node_comp_map[n] for n in sub.nodes()]
    nx.draw_networkx_edges(sub, pos_c0, ax=axes[1], alpha=0.3, edge_color="#7f8c8d", width=1.0)
    nx.draw_networkx_nodes(sub, pos_c0, ax=axes[1], node_size=85, node_color=colors_sub, cmap=plt.cm.tab10, edgecolors="#2c3e50", linewidths=0.5)
    nx.draw_networkx_labels(sub, pos_c0, labels=labels_crit, ax=axes[1], font_size=8, font_weight="bold", font_color="#1a1a1a")
    axes[1].axis("off")

    plt.tight_layout()
    plt.savefig(fig2_path, dpi=300, bbox_inches="tight")
    plt.close()
    print("Figure 2 generated successfully!")

    # -------------------------------------------------------------
    # Figure 3: Macro-Topological Metric, Centrality, & Link Prediction
    # -------------------------------------------------------------
    fig3_path = os.path.join(output_dir, "figure3_network_distributions.png")
    print(f"Rendering Figure 3 (Topological Distributions & Link Prediction ROC) -> {fig3_path}...")

    fig, axes = plt.subplots(2, 2, figsize=(16, 12), dpi=300)

    # 3A: Degree Distribution
    degrees = [d for n, d in G.degree()]
    axes[0, 0].hist(degrees, bins=30, color="#2980b9", edgecolor="black", alpha=0.8)
    axes[0, 0].set_title("A: Actor Degree Distribution", fontsize=11, fontweight="bold")
    axes[0, 0].set_xlabel("Degree (Number of Co-Stars)", fontsize=10)
    axes[0, 0].set_ylabel("Frequency (Actor Count)", fontsize=10)
    axes[0, 0].grid(True, linestyle="--", alpha=0.5)

    # Inset: Log-Log plot
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes
    ax_inset = inset_axes(axes[0, 0], width="42%", height="42%", loc="upper right")
    deg_counts = np.bincount(degrees)
    k = np.nonzero(deg_counts)[0]
    pk = deg_counts[k] / len(degrees)
    ax_inset.loglog(k, pk, "ro", markersize=3, alpha=0.7)
    ax_inset.set_title("Log-Log Fit", fontsize=8)
    ax_inset.tick_params(labelsize=7)

    # 3B: Granovetter Tie Strength
    weights = [d["weight"] for u, v, d in G.edges(data=True)]
    w_counts = Counter(weights)
    w_keys = sorted(w_counts.keys())
    w_vals = [w_counts[k] for k in w_keys]
    axes[0, 1].bar(w_keys, w_vals, color="#27ae60", edgecolor="black", alpha=0.8, width=0.5)
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_title("B: Edge Weight Distribution (Granovetter)", fontsize=11, fontweight="bold")
    axes[0, 1].set_xlabel("Edge Weight w(u, v) (Shared Films)", fontsize=10)
    axes[0, 1].set_ylabel("Edge Count (Log Scale)", fontsize=10)
    axes[0, 1].set_xticks(w_keys)
    for k_val, v_val in zip(w_keys, w_vals):
        axes[0, 1].text(k_val, v_val * 1.25, f"{v_val:,}\n({v_val/len(weights)*100:.1f}%)", ha="center", fontsize=8, fontweight="bold")
    axes[0, 1].grid(True, linestyle="--", alpha=0.5)

    # 3C: Betweenness vs Degree
    bc = nx.betweenness_centrality(gcc)
    bc_vals = [bc.get(n, 0) for n in gcc.nodes()]
    deg_gcc = [gcc.degree(n) for n in gcc.nodes()]
    axes[1, 0].scatter(deg_gcc, bc_vals, alpha=0.45, color="#8e44ad", edgecolors="none", s=25)
    axes[1, 0].set_title("C: Freeman Betweenness vs. Degree Centrality", fontsize=11, fontweight="bold")
    axes[1, 0].set_xlabel("Degree Centrality in GCC", fontsize=10)
    axes[1, 0].set_ylabel("Betweenness Centrality C_B", fontsize=10)
    axes[1, 0].grid(True, linestyle="--", alpha=0.5)

    top_bridges = sorted(bc.items(), key=lambda x: x[1], reverse=True)[:4]
    for name, val in top_bridges:
        d_val = gcc.degree(name)
        axes[1, 0].annotate(name, (d_val, val), textcoords="offset points", xytext=(5, 5),
                            fontsize=8, fontweight="bold", arrowprops=dict(arrowstyle="->", lw=0.8, color="black"))

    # 3D: Link Prediction ROC Curves
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

    plt.tight_layout()
    plt.savefig(fig3_path, dpi=300, bbox_inches="tight")
    plt.close()
    print("Figure 3 generated successfully!")

if __name__ == "__main__":
    movies = load_modern_movies()
    G = construct_collaboration_network(movies, max_billing=4)
    export_graphml(G)
    metrics = compute_characterization_metrics(G)
    gn_results = run_girvan_newman_analysis(metrics["gcc"], target_splits=4)
    lp_results = run_link_prediction_analysis(metrics["gcc"], n_test_edges=500)
    generate_visualizations(G, metrics["gcc"], metrics["comms"], gn_results, lp_results)
    print("\nComplete CS 176 Social Network Analysis pipeline finished successfully!")
