// Written by AI (OpenAI Codex)
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        int n;
        cin >> n;
        vector<long long> c(n), v(n);
        for (auto &x : c) cin >> x;
        for (auto &x : v) cin >> x;

        int answer = 0;
        int evenPiles = 0;
        vector<long long> remaining;
        for (int i = 0; i < n; ++i) {
            if (c[i] == 1) answer += v[i];
            else {
                remaining.push_back(v[i]);
                if (c[i] % 2 == 0) ++evenPiles;
            }
        }
        sort(remaining.rbegin(), remaining.rend());
        int firstIndex = evenPiles & 1;
        for (int i = firstIndex; i < (int)remaining.size(); i += 2) {
            answer += remaining[i];
        }
        cout << answer << '\n';
    }
}
