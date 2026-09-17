#include "testlib.h"
#include <bits/stdc++.h>
using namespace std;

typedef long long ll;

int main(int argc, char* argv[]) {
    registerGen(argc, argv, 1);

    int n = opt<int>("n");
    int m = opt<int>("m");
    int maxVal = opt<int>("maxval", 1000000000);
    string type = opt<string>("type", "random");

    vector<ll> a(n);
    for (int i = 0; i < n; i++) {
        a[i] = rnd.next(0LL, (ll)maxVal);
    }

    vector<pair<int,int>> edges;
    set<pair<int,int>> edge_set;

    auto add_edge = [&](int u, int v) {
        if (u > v) swap(u, v);
        if (edge_set.count({u, v})) return;
        edge_set.insert({u, v});
        edges.push_back({u, v});
    };

    if (type == "tree") {
        // Generate random tree (n-1 edges)
        for (int i = 2; i <= n; i++) {
            int p = rnd.next(1, i - 1);
            add_edge(p, i);
        }
    } else if (type == "path") {
        // Line graph
        for (int i = 1; i < n; i++) {
            add_edge(i, i + 1);
        }
    } else if (type == "cycle") {
        // Simple cycle
        for (int i = 1; i < n; i++) {
            add_edge(i, i + 1);
        }
        add_edge(n, 1);
    } else if (type == "complete") {
        // Complete graph (or as many edges as m allows)
        for (int i = 1; i <= n && (int)edges.size() < m; i++) {
            for (int j = i + 1; j <= n && (int)edges.size() < m; j++) {
                add_edge(i, j);
            }
        }
    } else if (type == "star") {
        // Star graph
        for (int i = 2; i <= n; i++) {
            add_edge(1, i);
        }
    } else if (type == "multiedge") {
        // Graph with multiple edges between same pairs
        set<int> used_nodes;
        for (int i = 0; i < m; i++) {
            int u = rnd.next(1, n);
            int v = rnd.next(1, n);
            while (u == v) v = rnd.next(1, n);
            if (u > v) swap(u, v);
            edges.push_back({u, v});
        }
    } else if (type == "selfloop") {
        // Graph with self-loops
        int real_edges = max(1, m * 2 / 3);
        for (int i = 0; i < real_edges; i++) {
            int u = rnd.next(1, n);
            int v = rnd.next(1, n);
            if (u == v) {
                edges.push_back({u, u});
            } else {
                if (u > v) swap(u, v);
                edges.push_back({u, v});
            }
        }
        // Add some self-loops
        while ((int)edges.size() < m) {
            int u = rnd.next(1, n);
            edges.push_back({u, u});
        }
    } else if (type == "random_tree_plus") {
        // Random tree + extra random edges (few bridges)
        for (int i = 2; i <= n; i++) {
            int p = rnd.next(1, i - 1);
            add_edge(p, i);
        }
        // Excess edges handled by final while loop
    } else if (type == "bridges") {
        // Graph with many bridges: several tree-like components connected by bridges
        for (int i = 2; i <= n; i++) {
            int p = rnd.next(max(1, i - 5), i - 1);
            add_edge(p, i);
        }
        // Excess edges handled by final while loop
    } else if (type == "nobridges") {
        // 2-edge-connected graph: add edges to a cycle
        for (int i = 1; i < n; i++) {
            add_edge(i, i + 1);
        }
        add_edge(n, 1);
        // Excess edges handled by final while loop
    } else if (type == "disconnected") {
        // Disconnected graph: several small components
        int comps = rnd.next(2, min(n / 2, 10));
        vector<int> perm(n);
        iota(perm.begin(), perm.end(), 0);
        shuffle(perm.begin(), perm.end());
        int idx = 0;
        for (int c = 0; c < comps; c++) {
            int sz = n / comps;
            if (c == comps - 1) sz = n - idx;
            for (int i = 1; i < sz; i++) {
                add_edge(perm[idx + i - 1] + 1, perm[idx + i] + 1);
            }
            idx += sz;
        }
    } else if (type == "boundary") {
        // Force boundary hits on a_i: at least one 0 and one maxVal
        // Build a cycle if enough nodes
        if (n >= 2) {
            for (int i = 1; i < n && (int)edges.size() < m; i++)
                add_edge(i, i + 1);
            if ((int)edges.size() < m)
                add_edge(n, 1);
        }
        // Fill remaining edges via the final generic loop
        // Set boundary values
        a[0] = 0;
        if (n >= 2) a[1] = maxVal;
        for (int i = 2; i < n; i++)
            a[i] = rnd.next(0LL, (ll)maxVal);
        shuffle(a.begin(), a.end());
    } else if (type == "zerovals") {
        // All values are 0
        for (int i = 0; i < n; i++) a[i] = 0;
        for (int i = 2; i <= n && (int)edges.size() < m; i++) {
            int p = rnd.next(1, i - 1);
            add_edge(p, i);
        }
    } else {
        // random: Erdos-Renyi
        for (int i = 0; i < m; i++) {
            int u = rnd.next(1, n);
            int v = rnd.next(1, n);
            if (u != v) add_edge(u, v);
        }
    }

    // Ensure we have exactly m edges (or as many as possible)
    while ((int)edges.size() < m) {
        int u = rnd.next(1, n);
        int v = rnd.next(1, n);
        if (u != v) {
            if (u > v) swap(u, v);
            edges.push_back({u, v});
        } else {
            edges.push_back({u, u});
        }
    }

    // Truncate if we generated too many
    if ((int)edges.size() > m) {
        shuffle(edges.begin(), edges.end());
        edges.resize(m);
    }

    // Output
    cout << n << " " << edges.size() << "\n";
    for (int i = 0; i < n; i++) {
        if (i > 0) cout << " ";
        cout << a[i];
    }
    cout << "\n";
    for (auto &e : edges) {
        cout << e.first << " " << e.second << "\n";
    }

    return 0;
}
