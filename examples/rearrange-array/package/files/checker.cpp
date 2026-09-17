#include "testlib.h"
#include <algorithm>
#include <vector>

using namespace std;

int main(int argc, char* argv[]) {
    registerTestlibCmd(argc, argv);

    int t = inf.readInt();

    for (int tc = 1; tc <= t; ++tc) {
        setTestCase(tc);

        int n = inf.readInt();

        vector<long long> a(n), b(n);
        for (long long& x : a) x = inf.readLong();
        for (long long& x : b) x = ouf.readLong();

        vector<long long> sortedA = a;
        vector<long long> sortedB = b;

        sort(sortedA.begin(), sortedA.end());
        sort(sortedB.begin(), sortedB.end());

        if (sortedA != sortedB) {
            quitf(
                _wa,
                "test case %d: output is not a permutation of the input",
                tc
            );
        }

        long long s1 = 0;
        long long s2 = 0;

        for (int i = 0; i < n; ++i) {
            s1 += (i % 2 == 0 ? b[i] : -b[i]);
            s2 += (i % 4 < 2 ? b[i] : -b[i]);
        }

        const int q = n / 4;

        long long bestS1 = 0;
        long long bestS2 = 0;

        for (int i = 0; i < n; ++i) {
            // Lowest half goes to negative S1 positions,
            // highest half goes to positive S1 positions.
            bestS1 += (i < 2 * q ? -sortedA[i] : sortedA[i]);

            // Sorted quarters:
            // Q1 -> (-S1, -S2)
            // Q2 -> (-S1, +S2)
            // Q3 -> (+S1, -S2)
            // Q4 -> (+S1, +S2)
            if (i < q) {
                bestS2 -= sortedA[i];
            } else if (i < 2 * q) {
                bestS2 += sortedA[i];
            } else if (i < 3 * q) {
                bestS2 -= sortedA[i];
            } else {
                bestS2 += sortedA[i];
            }
        }

        if (s1 != bestS1) {
            quitf(
                _wa,
                "test case %d: S1 is not maximum; expected %lld, found %lld",
                tc,
                bestS1,
                s1
            );
        }

        if (s2 != bestS2) {
            quitf(
                _wa,
                "test case %d: S2 is not maximum among S1-optimal "
                "permutations; expected %lld, found %lld",
                tc,
                bestS2,
                s2
            );
        }
    }

    if (!ouf.seekEof()) {
        quitf(_wa, "extra output after the last test case");
    }

    quitf(
        _ok,
        "all test cases contain lexicographically optimal permutations"
    );
}