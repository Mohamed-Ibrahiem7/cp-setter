#include <iostream>
#include <map>

using namespace std;

map<long long, pair<int, int>> c;

pair<int, int> ask(long long t) {
    if (c.count(t)) return c[t];
    cout << "? " << t << endl;
    int p, d;
    cin >> p >> d;
    if (p == -2 && d == -2) exit(0);
    return c[t] = {p, d};
}

void solve() {
    c.clear();
    long long t1 = -1, t2 = -1;
    long long l = 1, r = 1e9;

    while (l <= r) {
        long long m = l + (r - l) / 2;
        pair<int, int> res = ask(m);
        int p = res.first, d = res.second;

        if (p == 0 && d == 1) {
            t1 = m;
            break;
        }
        if (p == 0 && d == -1) {
            t2 = m;
            r = m - 1;
            continue;
        }
        if (d <= 0) {
            r = m - 1;
        } else {
            if (p == 1) r = m - 1;
            else l = m + 1;
        }
    }

    l = 1, r = 1e9;
    while (l <= r) {
        if (t2 != -1) break;
        long long m = l + (r - l) / 2;
        pair<int, int> res = ask(m);
        int p = res.first, d = res.second;

        if (p == 0 && d == -1) {
            t2 = m;
            break;
        }
        if (p == 0 && d == 1) {
            l = m + 1;
            continue;
        }
        if (d >= 0) {
            l = m + 1;
        } else {
            if (p == 1) l = m + 1;
            else r = m - 1;
        }
    }

    cout << "! " << t1 << " " << t2 << endl;
}

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    int t;
    cin >> t;
        while (t--) {
            solve();
        }
    
    return 0;
}