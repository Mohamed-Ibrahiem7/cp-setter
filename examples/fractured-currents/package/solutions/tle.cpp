#include <bits/stdc++.h>
using namespace std;

typedef long long ll;

const int MOD = 1000000007;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<ll> a(n + 1);
    for (int i = 1; i <= n; i++) cin >> a[i];

    vector<pair<int,int>> edges(m);
    for (int i = 0; i < m; i++) {
        cin >> edges[i].first >> edges[i].second;
    }

    ll ans = LLONG_MAX;

    for (int skip = 0; skip < m; skip++) {
        // Build DSU excluding edge 'skip'
        vector<int> parent(n + 1);
        iota(parent.begin(), parent.end(), 0);
        function<int(int)> find = [&](int x) {
            return parent[x] == x ? x : parent[x] = find(parent[x]);
        };
        auto unite = [&](int x, int y) {
            x = find(x), y = find(y);
            if (x != y) parent[x] = y;
        };

        for (int i = 0; i < m; i++) {
            if (i == skip) continue;
            int u = edges[i].first, v = edges[i].second;
            unite(u, v);
        }

        // Group nodes by component
        vector<vector<int>> comps(n + 1);
        for (int i = 1; i <= n; i++) {
            comps[find(i)].push_back(i);
        }

        ll score = 0;
        for (int c = 1; c <= n; c++) {
            if (comps[c].size() < 2) continue;
            auto &comp = comps[c];
            int sz = comp.size();
            for (int i = 0; i < sz; i++) {
                for (int j = i + 1; j < sz; j++) {
                    int u = comp[i], v = comp[j];
                    score += a[u] ^ a[v];
                }
            }
        }

        if (score < ans) ans = score;
    }

    cout << ans % MOD << '\n';

    return 0;
}
