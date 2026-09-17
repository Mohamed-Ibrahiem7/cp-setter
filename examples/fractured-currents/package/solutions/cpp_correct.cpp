#include <bits/stdc++.h>
using namespace std;

typedef long long ll;

const int MOD = 1000000007;
const int B = 30;

vector<vector<pair<int,int>>> g;
vector<ll> a;
vector<int> tin, low, sub_sz;
vector<vector<int>> sub;
vector<int> parent_dfs, parent_edge_dfs, next_edge_dfs;
int timer;
vector<int> comp_bridges;

void dfs(int root) {
    vector<int> stack;
    stack.push_back(root);
    parent_dfs[root] = 0;

    while (!stack.empty()) {
        int u = stack.back();

        if (tin[u] == -1) {
            tin[u] = low[u] = ++timer;
            sub_sz[u] = 1;
            for (int b = 0; b < B; ++b) sub[u][b] = (a[u] >> b) & 1;
        }

        if (next_edge_dfs[u] < (int)g[u].size()) {
            auto [v, eid] = g[u][next_edge_dfs[u]++];
            if (eid == parent_edge_dfs[u]) continue;
            if (tin[v] != -1) {
                low[u] = min(low[u], tin[v]);
            } else {
                parent_dfs[v] = u;
                parent_edge_dfs[v] = eid;
                stack.push_back(v);
            }
            continue;
        }

        stack.pop_back();
        if (parent_dfs[u] != 0) {
            int p = parent_dfs[u];
            low[p] = min(low[p], low[u]);
            sub_sz[p] += sub_sz[u];
            for (int b = 0; b < B; ++b) sub[p][b] += sub[u][b];
            if (low[u] > tin[p]) comp_bridges.push_back(u);
        }
    }
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    a.resize(n + 1);
    for (int i = 1; i <= n; i++) cin >> a[i];

    g.resize(n + 1);
    for (int i = 0; i < m; i++) {
        int u, v;
        cin >> u >> v;
        g[u].push_back({v, i});
        if (u != v) g[v].push_back({u, i});
    }

    tin.assign(n + 1, -1);
    low.assign(n + 1, -1);
    sub_sz.assign(n + 1, 0);
    sub.assign(n + 1, vector<int>(B, 0));
    parent_dfs.assign(n + 1, 0);
    parent_edge_dfs.assign(n + 1, -1);
    next_edge_dfs.assign(n + 1, 0);
    timer = 0;

    ll total_score = 0;
    ll max_loss = 0;

    for (int i = 1; i <= n; i++) {
        if (tin[i] != -1) continue;

        comp_bridges.clear();
        dfs(i);

        ll comp_sz = sub_sz[i];

        for (int b = 0; b < B; b++) {
            ll ones = sub[i][b];
            ll zeros = comp_sz - ones;
            total_score += ones * zeros * (1LL << b);
        }

        for (int child : comp_bridges) {
            ll child_sz = sub_sz[child];
            ll other_sz = comp_sz - child_sz;
            ll cross = 0;
            for (int b = 0; b < B; b++) {
                ll child_one = sub[child][b];
                ll child_zero = child_sz - child_one;
                ll other_one = sub[i][b] - child_one;
                ll other_zero = other_sz - other_one;
                cross += (child_one * other_zero + child_zero * other_one) * (1LL << b);
            }
            if (cross > max_loss) max_loss = cross;
        }
    }

    ll ans = (total_score - max_loss) % MOD;
    if (ans < 0) ans += MOD;

    cout << ans << '\n';

    return 0;
}
