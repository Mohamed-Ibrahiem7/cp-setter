#include "testlib.h"

const int T_MAX = 10000;
const int N_MAX = 200000;
const int SUM_N_MAX = 200000;
const int A_MAX = 1000000000;

int main(int argc, char* argv[]) {
    registerValidation(argc, argv);

    int t = inf.readInt(1, T_MAX, "t");
    inf.readEoln();

    int sum_n = 0;
    for (int tc = 1; tc <= t; tc++) {
        setTestCase(tc);

        int n = inf.readInt(1, N_MAX, "n");
        inf.readEoln();

        sum_n += n;
        ensuref(sum_n <= SUM_N_MAX,
                "sum of n over all test cases exceeds %d", SUM_N_MAX);

        for (int i = 0; i < n; i++) {
            inf.readInt(1, A_MAX, "a_i");
            if (i + 1 < n) inf.readSpace();
        }
        inf.readEoln();

        // TODO: structural guarantees this problem states, for example
        //   ensuref(k <= n, "k must not exceed n");
        //   a permutation check, a DSU tree check, distinctness, sortedness.
        // Every bound and guarantee in the statement belongs here, and nothing else.
    }

    inf.readEof();
    return 0;
}
