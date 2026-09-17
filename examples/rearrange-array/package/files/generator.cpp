#include "testlib.h"
#include <bits/stdc++.h>
using namespace std;

int main(int argc, char* argv[]) {
    registerGen(argc, argv, 1);

    int t = opt<int>("t", 1);
    int max_n = opt<int>("max_n", 200000);
    int max_val = opt<int>("max_val", 1000000000);
    string mode = opt<string>("mode", "random");

    max_n = (max_n / 4) * 4;

    cout << t << "\n";
    int rem_n = max_n;

    for (int tc = 0; tc < t; ++tc) {
        int n;
        if (tc == t - 1) {
            n = rem_n;
        } else {
            int max_blocks = (rem_n - 4 * (t - 1 - tc)) / 4;
            int blocks = rnd.wnext(1, max(1, max_blocks), 3);
            n = blocks * 4;
        }
        rem_n -= n;

        vector<int> a(n);
        if (mode == "random") {
            for (int i = 0; i < n; ++i) a[i] = rnd.next(-max_val, max_val);
        } else if (mode == "sorted") {
            for (int i = 0; i < n; ++i) a[i] = rnd.next(-max_val, max_val);
            sort(a.begin(), a.end());
        } else if (mode == "rev_sorted") {
            for (int i = 0; i < n; ++i) a[i] = rnd.next(-max_val, max_val);
            sort(a.rbegin(), a.rend());
        } else if (mode == "identical") {
            int val = rnd.next(-max_val, max_val);
            fill(a.begin(), a.end(), val);
        } else if (mode == "extremes") {
            for (int i = 0; i < n; ++i) {
                a[i] = rnd.next(0, 1) ? max_val : -max_val;
            }
        }

        cout << n << "\n";
        for (int i = 0; i < n; ++i) {
            cout << a[i] << (i + 1 == n ? "" : " ");
        }
        cout << "\n";
    }

    return 0;
}