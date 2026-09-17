#include <bits/stdc++.h>
using namespace std;

void solve() {
    int n;
    cin >> n;
    vector<long long> a(n);
    for (int i = 0; i < n; ++i) cin >> a[i];

    sort(a.begin(), a.end());
    vector<long long> best_b = a;
    long long best_score = -4e18;

    // Brute-force all permutations
    do {
        long long s1 = 0, s2 = 0;
        for (int i = 0; i < n; ++i) {
            int sign1 = (i % 2 == 0) ? 1 : -1;
            int sign2 = ((i / 2) % 2 == 0) ? 1 : -1;
            s1 += sign1 * a[i];
            s2 += sign2 * a[i];
        }
        
        long long total = s1 + s2;
        if (total > best_score) {
            best_score = total;
            best_b = a;
        }
    } while (next_permutation(a.begin(), a.end()));

    for (int i = 0; i < n; ++i) {
        cout << best_b[i] << (i + 1 == n ? "" : " ");
    }
    cout << "\n";
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    if (cin >> t) {
        while (t--) solve();
    }
    return 0;
}