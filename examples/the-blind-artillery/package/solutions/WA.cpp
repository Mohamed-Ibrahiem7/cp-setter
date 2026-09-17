#include <bits/stdc++.h>
using namespace std;

void solve() {
    int t1 = -1, t2 = -1;
    
    int l = 1, r = 1e9;
    while (l <= r) {
        int m = l + (r - l) / 2;
        cout << "? " << m << endl;
        
        int p, d;
        cin >> p >> d;
        
        if (p == -2 && d == -2) exit(0);
        
        if (p == 0 && d == 1) {
            t1 = m;
            break;
        }
        
        if (p == -1 && d == 1) {
            l = m + 1;
        } else {
            r = m - 1;
        }
    }
    
    l = t1 + 1; // Start searching for t2 strictly after t1
    r = 1e9;
    while (l <= r) {
        int m = l + (r - l) / 2;
        cout << "? " << m << endl;
        
        int p, d;
        cin >> p >> d;
        
        if (p == -2 && d == -2) exit(0);
        
        if (p == 0 && d == -1) {
            t2 = m;
            break;
        }
        
        if (p == -1 && d == -1) {
            r = m - 1;
        } else {
            l = m + 1;
        }
    }
    
    int wrong_t1 = (t1 == 1e9) ? 1 : t1 + 1;
    int wrong_t2 = (t2 == 1e9) ? 2 : t2 + 1;
    
    cout << "! " << wrong_t1 << " " << wrong_t2 << endl;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    
    int tc;
    if (cin >> tc) {
        while (tc--) {
            solve();
        }
    }
    return 0;
}