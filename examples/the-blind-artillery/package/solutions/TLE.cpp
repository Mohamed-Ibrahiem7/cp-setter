// brute.cpp
 
#include <bits/stdc++.h>
using namespace std;
 
using ll = long long;

int query_count = 0;
 
int ask(ll t) {
    query_count++;

    if (query_count > 80) {
        return -1; 
    }

    cout << "? " << t << endl;
    cout.flush();
 
    int P, D;
    cin >> P >> D;
 
    if (P == -2 && D == -2)
        exit(0);
 
    return P;
}
 
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
 
    int T;
    cin >> T;
 
    while (T--) {
        query_count = 0; // Reset query count for each test case
        ll t1 = -1, t2 = -1;
 
        for (ll t = 1; t <= 1000000000LL; t++) {
 
            int P = ask(t);
 
            if (P == 0) {
                if (t1 == -1)
                    t1 = t;
                else {
                    t2 = t;
                    break;
                }
            }
        }
 
        cout << "! " << t1 << ' ' << t2 << endl;
        cout.flush();
    }
 
    return 0;
}