from itertools import accumulate, product
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from graph_connectivity.clustering import ClusterProblem
from graph_connectivity.explore_problem import ExplorationProblem

def animate(graph, traj, conn, 
            node_colors=None,     # dict t,v : color
            node_explored=None,   # dict t,v : bool
            titles=None,          # dict t: title
            unkown_color='white',
            STEP_T=1, FPS=20, size=10,
            filename="animation.mp4"):

    T = max(t for r,t in traj)

    # Colors for robots
    rob_col = plt.cm.rainbow(np.linspace(0, 1, len(graph.agents)))

    # Build dictionary time -> positions
    rob_pos = {t : np.array([[graph.nodes[traj[r,t]]['x'], 
                             graph.nodes[traj[r,t]]['y']] for r in graph.agents]) 
               for t in range(T+1)}

    # Connectivity colors: t,v1,v2 -> [c0 c1 c2]
    conn_col = { (t,v1,v2) : [] for t, conn_list in conn.items() for (v1, v2, b) in conn_list }
    for t, conn_list in conn.items():
        for (v1, v2, b) in conn_list:
            conn_col[t, v1, v2].append(rob_col[b])

    # Node styling: t -> [c0 c1 ... cV]
    if node_colors is not None:
        nod_col = {t : [node_colors[t,v] for v in graph.nodes] for t in range(T+1)}
    else:
        nod_col = {t : ['white' for v in graph.nodes] for t in range(T+1)}
    nod_ecol = {t : ['black' for v in graph.nodes] for t in range(T+1)}
    nod_lcol = {t : ['black' for v in graph.nodes] for t in range(T+1)}    
    nod_thick = {t : [1. for v in graph.nodes] for t in range(T+1)}

    # Edge styling
    tran_edge_alpha = {t : [1. for v in graph.tran_edges()] for t in range(T+1)}
    tran_edge_color = {t : ['black' for v in graph.tran_edges()] for t in range(T+1)}  
    tran_edge_thick = {t : [1. for v in graph.tran_edges()] for t in range(T+1)}          
    conn_edge_alpha = {t : [1. for v in graph.conn_edges()] for t in range(T+1)}

    # Style exploration colors
    if node_explored is not None:
        for t in range(T+1):
            for i, v in enumerate(graph.nodes):
                if not node_explored[t, v]:                            # Hidden node
                    nod_col[t][i] = unkown_color
                    nod_ecol[t][i] = unkown_color
                    nod_lcol[t][i] = unkown_color

            for i, (v1, v2) in enumerate(graph.tran_edges()):
                if not node_explored[t, v1]:                           # Hidden edge
                    tran_edge_alpha[t][i] = 0.
                if node_explored[t, v1] and not node_explored[t, v2]:  # Frontier node/edge
                    tran_edge_color[t][i] = 'orange' 
                    nod_ecol[t][list(graph.nodes).index(v1)] = 'orange'                    
                    tran_edge_thick[t][i] = 2.5 
                    nod_thick[t][list(graph.nodes).index(v1)] = 2.5 

            for i, (v1, v2) in enumerate(graph.conn_edges()):
                if (not node_explored[t, v1]) or (not node_explored[t, v2]):
                    conn_edge_alpha[t][i] = 0.

    ########## INITIAL PLOT ##################

    dict_pos = {n: (graph.nodes[n]['x'], graph.nodes[n]['y']) for n in graph}
    npos = np.array([dict_pos[i] for i in graph.nodes])

    fig, ax = plt.subplots(1, 1, figsize=(size, size))
    ax.axis('off')

    # nodes
    coll_npos = ax.scatter(npos[:,0], npos[:,1], s=350, marker='o',
                           c=nod_col[0], zorder=5, alpha=1,
                           linewidths=1.0, edgecolors=np.full(len(graph.nodes), 'black'))
    # node labels
    coll_ntext = [ax.text(npos[i,0], npos[i,1], str(n),
                          horizontalalignment='center',
                          verticalalignment='center',
                          zorder=5, size=8, color='black',
                          family='sans-serif', weight='bold', alpha=1.0)
                  for i, n in enumerate(graph.nodes)]

    coll_tran_edge = nx.draw_networkx_edges(graph, dict_pos, ax=ax, edgelist=list(graph.tran_edges()),
                                            connectionstyle='arc', edge_color='black')
    coll_conn_edge = nx.draw_networkx_edges(graph, dict_pos, ax=ax, edgelist=list(graph.conn_edges()),
                                            edge_color='black')
    title_field = ax.text((max(npos[:,0])+min(npos[:,0]))/2, 
                          max(npos[:,1]), "",
                          horizontalalignment='center',
                          verticalalignment='top',
                          zorder=5, size=14, color='black',
                          family='sans-serif', weight='bold', alpha=1.0)
    time_field = ax.text((max(npos[:,0])+min(npos[:,0]))/2, 
                         max(npos[:,1])-0.5, "",
                         horizontalalignment='center',
                         verticalalignment='top',
                         zorder=5, size=14, color='black',
                         family='sans-serif', weight='bold', alpha=1.0)

    if coll_conn_edge is not None:
        for cedge in coll_conn_edge:
            cedge.set_connectionstyle("arc3,rad=0.25")
            cedge.set_linestyle('dashed')

    # initial colors
    for i, (v1, v2) in enumerate(graph.conn_edges()):
        coll_conn_edge[i].set_alpha(conn_edge_alpha[0][i])
    for i, (v1, v2) in enumerate(graph.tran_edges()):
        coll_tran_edge[i].set_alpha(tran_edge_alpha[0][i])
    coll_npos.set_facecolor(nod_col[0])
    coll_npos.set_edgecolor(nod_ecol[0])
    for i,n in enumerate(graph.nodes):
        coll_ntext[i].set_color(nod_ecol[0][i])

    # robot nodes
    coll_rpos = ax.scatter(rob_pos[0][:,0], rob_pos[0][:,1], s=140, marker='o',
                           c=rob_col, zorder=7, alpha=1,
                           linewidths=2, edgecolors='black')
    # robot labels
    coll_rtext = [ax.text(rob_pos[0][i,0], rob_pos[0][i,1], str(r),
                         horizontalalignment='center',
                         verticalalignment='center',
                         zorder=10, size=8, color='k',
                         family='sans-serif', weight='bold', alpha=1.0)
                 for i, r in enumerate(graph.agents)]

    ########## LOOP #############

    FRAMES_PER_STEP = max(2, int(STEP_T * FPS))
    total_time = T + 2

    def animate(i):
        t = int(i / FRAMES_PER_STEP)
        anim_idx = i % FRAMES_PER_STEP
        alpha = anim_idx / FRAMES_PER_STEP

        if anim_idx == 1:
            print("Animating step {}/{}".format(t+1, total_time))

        if anim_idx == 0:
            # node styling
            coll_npos.set_facecolor(nod_col[min(T, t)])
            coll_npos.set_edgecolor(nod_ecol[min(T,t)])
            coll_npos.set_linewidth(nod_thick[min(T,t)])

            for i,n in enumerate(graph.nodes):
                coll_ntext[i].set_color(nod_lcol[min(T,t)][i])

            # connectivity edge styling
            for i, (v1, v2) in enumerate(graph.conn_edges()):
                coll_conn_edge[i].set_alpha(conn_edge_alpha[min(T, t)][i])
                coll_conn_edge[i].set_color("black")
                coll_conn_edge[i].set_linewidth(1)

            # transition edge styling
            for i, (v1, v2) in enumerate(graph.tran_edges()):
                coll_tran_edge[i].set_alpha(tran_edge_alpha[min(T, t)][i])
                coll_tran_edge[i].set_color(tran_edge_color[min(T, t)][i])
                coll_tran_edge[i].set_linewidth(tran_edge_thick[min(T, t)][i])

            # text/time fields
            if titles is not None:
                if t in titles:
                    title_field.set_text(titles[t])
            time_field.set_text("t={}".format(t))

        # Update connectivity edge colors if there is flow information
        for i, (v1, v2) in enumerate(graph.conn_edges()):
            if (t, v1, v2) in conn_col:
                col_list = conn_col[t,v1,v2]
                coll_conn_edge[i].set_color(col_list[int(10 * alpha) % len(col_list)])
                coll_conn_edge[i].set_linewidth(2.5)

        # Update robot node and label positions
        pos = (1-alpha) * rob_pos[min(T, t)] + alpha * rob_pos[min(T, t+1)]
        coll_rpos.set_offsets(pos)
        for i in range(len(graph.agents)):
            coll_rtext[i].set_x(pos[i, 0])
            coll_rtext[i].set_y(pos[i, 1])


    ani = animation.FuncAnimation(fig, animate, range(total_time * FRAMES_PER_STEP),
                                  interval=1000/FPS, blit=False)
    ani.save(filename)


def animate_cluster(graph, traj, conn, subgraphs, **kwargs):
    
    T = max(t for r,t in traj)

    clu_col = dict(zip(subgraphs, plt.cm.gist_rainbow(np.linspace(0, 1, len(subgraphs)))))
    node_colors = {(t, v) : clu_col[c] for c,v_list in subgraphs.items() 
                                       for v in v_list
                                       for t in range(T+1)}

    return animate(graph, traj, conn, node_colors=node_colors, **kwargs)


def animate_cluster_sequence(graph, problem_list, **kwargs):

    # Use a one to put one time step between problems
    start_time = [0] + list(accumulate([problem.T + 1 for problem in problem_list]))

    T = start_time[-1]

    ### Merge trajectories
    traj = {}
    for i in range(len(problem_list)):
        for (r, t), v in problem_list[i].traj.items():
            traj[r, start_time[i] + t] = v

    # Fill in missing values with blanks
    for r, t in product(graph.agents, range(T+1)):
        if not (r,t) in traj:
            traj[r,t] = traj[r,t-1]

    ### Merge connectivity info
    conn = {}
    for i in range(len(problem_list)):
        if problem_list[i].conn is not None:
            for t, conn_list in problem_list[i].conn.items():
                conn[start_time[i] + t] = conn_list

    ### Prepare node colors
    num_clusters = max(len(problem.subgraphs) for problem in problem_list if isinstance(problem, ClusterProblem))
    clu_col = plt.cm.gist_rainbow(np.linspace(0, 1, num_clusters))
    node_colors = {(0, v) : 'white' for v in graph.nodes}
    for i, problem in enumerate(problem_list):
        if isinstance(problem, ClusterProblem):
            for j, v_list in enumerate(problem.subgraphs.values()):
                for v in v_list:
                    for t in range(start_time[i], start_time[i] + problem.T):
                        node_colors[t, v] = clu_col[j]
    
    # Fill in missing values with blanks
    for i, v in enumerate(graph.nodes):
        for t in range(T+1):
            if (t, v) not in node_colors:
                node_colors[t, v] = node_colors[t-1, v]

    ### Prepare explored/unexplored
    node_explored = { (0, v) : False for v in graph.nodes }
    for i, problem in enumerate(problem_list):
        if isinstance(problem, ExplorationProblem):
            for t, g in enumerate(problem.graph_list):
                for n in g.nodes:
                    if g.nodes[n]['known']:
                        node_explored[start_time[i] + t, n] = True

    # Fill in missing values with blanks
    for v in graph.nodes:
        for t in range(T+1):
            if (t, v) not in node_explored:
                node_explored[t, v] = node_explored[t-1, v]

    titles = {}
    out = True
    for i, problem in enumerate(problem_list):
        if isinstance(problem, ExplorationProblem):
            titles[start_time[i]] = "Exploration"
        if isinstance(problem, ClusterProblem):
            titles[start_time[i]] = "To Frontiers" if out else "To base"
            out = not out

    return animate(graph, traj, conn, node_colors=node_colors, 
                   node_explored=node_explored, titles=titles, 
                   **kwargs)
