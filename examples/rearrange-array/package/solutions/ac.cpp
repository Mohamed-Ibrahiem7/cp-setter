#include <bits/stdc++.h>
using namespace std;

void solve() {
    int n;
    if (!(cin >> n)) return;

    vector<long long> a(n);
    for (int i = 0; i < n; ++i) {
        cin >> a[i];
    }

    sort(a.begin(), a.end());

    int m = n / 4;
    vector<long long> b(n);

    // Q1: a[0 ... m-1]
    // Q2: a[m ... 2m-1]
    // Q3: a[2m ... 3m-1]
    // Q4: a[3m ... 4m-1]
    for (int i = 0; i < m; ++i) {
        b[4 * i + 0] = a[3 * m + i]; // Q4: (+, +)
        b[4 * i + 1] = a[m + i];     // Q2: (-, +)
        b[4 * i + 2] = a[2 * m + i]; // Q3: (+, -)
        b[4 * i + 3] = a[i];         // Q1: (-, -)
    }

    for (int i = 0; i < n; ++i) {
        cout << b[i] << (i + 1 == n ? "" : " ");
    }
    cout << "\n";
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int t;
    if (cin >> t) {
        while (t--) {
            solve();
        }
    }
    return 0;
}