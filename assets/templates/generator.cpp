#include "testlib.h"
#include <bits/stdc++.h>

using namespace std;

// Usage:  gen -t <cases> -maxn <per-case cap> -sumn <aggregate budget> [-mode <name>]
//
//   mode  random     uniform values
//         sorted     non-decreasing, for solutions that assume input order
//         equal      every value identical, for tie handling
//         twovalue   only two distinct values, for counting and dedup bugs
//         extremes   only the smallest and largest legal values, for overflow
//
// Add one mode per assumption a contestant could make, and say here what each
// one is for. registerGen seeds rnd from the whole command line, so every line
// in the script must differ in at least one argument.

int main(int argc, char* argv[]) {
    registerGen(argc, argv, 1);

    int t = opt<int>("t");
    int maxn = opt<int>("maxn");
    int sumn = opt<int>("sumn");
    int maxval = opt<int>("maxval", 1000000000);
    string mode = opt<string>("mode", "random");

    ensuref(t >= 1 && maxn >= 1, "t and maxn must be positive");
    ensuref(sumn >= t && (long long)t * maxn >= sumn,
            "sumn=%d is not reachable with t=%d, maxn=%d", sumn, t, maxn);

    // Split the aggregate budget so the sizes total exactly sumn, each in [1, maxn].
    vector<int> sizes;
    int remaining = sumn;
    for (int i = 0; i < t; i++) {
        int lo = max(1, remaining - (t - i - 1) * maxn);
        int hi = min(maxn, remaining - (t - i - 1));
        if (lo > hi) lo = hi;
        int n = rnd.next(lo, hi);
        sizes.push_back(n);
        remaining -= n;
    }
    shuffle(sizes.begin(), sizes.end());

    println(t);
    for (int n : sizes) {
        println(n);

        vector<int> a(n);
        for (int i = 0; i < n; i++) {
            if (mode == "equal")
                a[i] = maxval;
            else if (mode == "twovalue")
                a[i] = rnd.next(0, 1) ? 1 : maxval;
            else if (mode == "extremes")
                a[i] = rnd.next(0, 1) ? 1 : maxval;
            else
                a[i] = rnd.next(1, maxval);
        }
        if (mode == "sorted")
            sort(a.begin(), a.end());

        println(a);
    }

    return 0;
}
