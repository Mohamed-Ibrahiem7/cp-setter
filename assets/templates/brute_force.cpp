#include <bits/stdc++.h>

using namespace std;

// Scratch reference for stress testing. Obviously correct beats fast: try every
// possibility, simulate directly, recompute from scratch. It only ever runs on
// tiny inputs, so readability is the only thing that matters here.

void solve() {
    int n;
    cin >> n;
    vector<long long> a(n);
    for (auto &x : a)
        cin >> x;

    long long best = LLONG_MIN;
    for (int mask = 0; mask < (1 << n); mask++) {
        long long cur = 0;
        for (int i = 0; i < n; i++)
            if (mask >> i & 1)
                cur += a[i];
        best = max(best, cur);
    }

    cout << best << '\n';
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--)
        solve();
    return 0;
}
