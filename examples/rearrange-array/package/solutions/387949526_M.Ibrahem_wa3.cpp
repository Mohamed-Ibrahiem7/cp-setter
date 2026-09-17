#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        vector<long long> a(n), b(n);
        for (auto &x : a) cin >> x;

        sort(a.begin(), a.end());
        for (int i = 0; i < n; i += 4) {
            b[i] = a[i + 3];
            b[i + 1] = a[i + 1];
            b[i + 2] = a[i + 2];
            b[i + 3] = a[i];
        }

        for (int i = 0; i < n; ++i)
            cout << b[i] << " \n"[i + 1 == n];
    }
}