#define main reference_main
#include <bits/stdc++.h>
using namespace std;
const long long MOD = 1000000007;

struct Edge {
  int u, v;
};

struct Solver {
  int n, m, timer = 0;
  vector<long long> a;
  vector<Edge> e;
  vector<vector<pair<int, int> > > g;
  vector<int> tin, low, sz;
  vector<array<int, 30> > ones;
  vector<int> bridgeChild;

  Solver(int n, int m) : n(n), m(m), a(n), e(m), g(n), tin(n, -1), low(n), sz(n), ones(n) {
  }

  long long run(bool parentVertexBug = false, bool allTree = false, bool assumeConnected = false) {
    long long initial = 0, best = 0;
    array<int, 30> global{};
    for (long long x: a)for (int b = 0; b < 30; b++)global[b] += (int) ((x >> b) & 1);
    vector<int> parent(n, -1), pe(n, -1), it(n);
    for (int root = 0; root < n; root++)if (tin[root] < 0) {
      int before = bridgeChild.size();
      tin[root] = low[root] = timer++;
      sz[root] = 1;
      for (int b = 0; b < 30; b++)ones[root][b] = (a[root] >> b) & 1;
      vector<int> st = {root};
      while (!st.empty()) {
        int v = st.back();
        if (it[v] < (int) g[v].size()) {
          auto [u,id] = g[v][it[v]++];
          if (parentVertexBug ? u == parent[v] : id == pe[v])continue;
          if (tin[u] != -1) {
            low[v] = min(low[v], tin[u]);
            continue;
          }
          parent[u] = v;
          pe[u] = id;
          tin[u] = low[u] = timer++;
          sz[u] = 1;
          for (int b = 0; b < 30; b++)ones[u][b] = (a[u] >> b) & 1;
          st.push_back(u);
        } else {
          st.pop_back();
          if (parent[v] != -1) {
            int p = parent[v];
            sz[p] += sz[v];
            for (int b = 0; b < 30; b++)ones[p][b] += ones[v][b];
            low[p] = min(low[p], low[v]);
            if (allTree || low[v] > tin[p])bridgeChild.push_back(v);
          }
        }
      }
      array<int, 30> tot = assumeConnected ? global : ones[root];
      int totalSize = assumeConnected ? n : sz[root];
      for (int b = 0; b < 30; b++)initial += 1LL * tot[b] * (totalSize - tot[b]) * (1LL << b);
      for (int z = before; z < (int) bridgeChild.size(); z++) {
        int u = bridgeChild[z];
        long long cut = 0;
        for (int b = 0; b < 30; b++) {
          long long o = ones[u][b], s = sz[u], O = tot[b];
          cut += (o * (totalSize - s - (O - o)) + (s - o) * (O - o)) * (1LL << b);
        }
        best = max(best, cut);
      }
    }
    if (assumeConnected) {
      initial = 0;
      for (int b = 0; b < 30; b++)initial += 1LL * global[b] * (n - global[b]) * (1LL << b);
    }
    return initial - best;
  }
};

int main() {
  ios::sync_with_stdio(false);
  cin.tie(nullptr);
  int n, m;
  cin >> n >> m;
  Solver s(n, m);
  for (auto &x: s.a)cin >> x;
  for (int i = 0; i < m; i++) {
    int u, v;
    cin >> u >> v;
    --u;
    --v;
    s.e[i] = {u, v};
    s.g[u].push_back({v, i});
    s.g[v].push_back({u, i});
  }
  long long z = s.run();
  cout << z % MOD << '\n';
  return 0;
}

#undef main
int main() {
  ios::sync_with_stdio(false);
  cin.tie(nullptr);
  int n, m;
  cin >> n >> m;
  Solver s(n, m);
  for (auto &x: s.a)cin >> x;
  for (int i = 0; i < m; i++) {
    int u, v;
    cin >> u >> v;
    --u;
    --v;
    s.e[i] = {u, v};
    s.g[u].push_back({v, i});
    s.g[v].push_back({u, i});
  }
  long long z = s.run(true, false, false);
  cout << z % MOD << '\n';
}
