#include "testlib.h"
using namespace std;

const int MAXN = 200000;
const int MAXVAL = 1000000000;

int main(int argc, char* argv[]) {
    registerValidation(argc, argv);

    int t = inf.readInt(1, 10000, "t");
    inf.readEoln();

    int sum_n = 0;
    for (int tc = 1; tc <= t; ++tc) {
        setTestCase(tc);
        int n = inf.readInt(4, MAXN, "n");
        ensuref(n % 4 == 0, "n must be divisible by 4");
        inf.readEoln();

        sum_n += n;
        ensuref(sum_n <= MAXN, "Sum of n exceeds %d", MAXN);

        for (int i = 1; i <= n; ++i) {
            inf.readInt(-MAXVAL, MAXVAL, format("a[%d]", i));
            if (i < n) inf.readSpace();
            else inf.readEoln();
        }
    }

    inf.readEof();
    return 0;
}