#include "testlib.h"
#include <bits/stdc++.h>
using namespace std;

int main(int argc, char* argv[]) {
    registerGen(argc, argv, 1);

    int t = opt<int>("t");
    int maxn = opt<int>("maxn");
    int sumn = opt<int>("sumn");

    vector<int> lens;
    int remaining = sumn;
    for (int i = 0; i < t; i++) {
        int lo = max(1, remaining - (t - i - 1) * maxn);
        int hi = min(maxn, remaining - (t - i - 1) * 1);
        if (lo > hi) lo = hi;
        int val = rnd.next(lo, hi);
        lens.push_back(val);
        remaining -= val;
    }
    shuffle(lens.begin(), lens.end());

    cout << t << '\n';
    for (int x : lens) {
        cout << x << '\n';
    }
    return 0;
}
