#include <bits/stdc++.h>
#define int long long
using namespace std;

void solve() {
    int n;
    cin >> n;
    
    vector<int> c(n);
    for (int i = 0; i < n; ++i) cin >> c[i];
    
    vector<int> v(n);
    for (int i = 0; i < n; ++i) cin >> v[i];
    
    int amr_score = 0;
    int safe_moves = 0;
    vector<int> endgame_treasures;
    
    for (int i = 0; i < n; ++i) {
        if (c[i] == 1) {
            // Amr sweeps all 1-problem sheets instantly because of the extra turn rule
            amr_score += v[i];
        } else {
            // A sheet with C_i >= 2 provides (C_i - 2) safe moves
            safe_moves += (c[i] - 2);
            endgame_treasures.push_back(v[i]);
        }
    }
    
    // Sort the remaining sheets in ascending order of value
    sort(endgame_treasures.begin(), endgame_treasures.end());
    
    // If total safe moves is EVEN, Amr makes the first suicide move.
    // If total safe moves is ODD, Zezo makes the first suicide move.
    bool amr_suicides = (safe_moves % 2 == 0);
    
    // The suicider gives the cheapest sheet to the opponent. 
    // The opponent takes it, gets an extra turn, and becomes the new suicider!
    // So the non-suicider gets indices 0, 2, 4... and the suicider gets 1, 3, 5...
    for (size_t i = 0; i < endgame_treasures.size(); ++i) {
        if (amr_suicides) {
            if (i % 2 == 1) amr_score += endgame_treasures[i];
        } else {
            if (i % 2 == 0) amr_score += endgame_treasures[i];
        }
    }
    
    cout << amr_score << "\n";
}

signed main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    int t; 
    if (cin >> t) {
        while (t--) solve();
    }
    return 0;
}