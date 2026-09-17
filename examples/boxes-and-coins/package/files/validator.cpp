#include "testlib.h"
#include <bits/stdc++.h>
using namespace std;

int main(int argc, char* argv[]) {
    registerValidation(argc, argv);

    int t = inf.readInt(1, 1000, "t");
    inf.readEoln();

    int sum_n = 0;
    for (int tc = 0; tc < t; tc++) {
        int n = inf.readInt(1, 5000, "n");
        inf.readEoln();
        sum_n += n;
        ensuref(sum_n <= 5000, "sum of n over all test cases must not exceed 5000");
    }

    inf.readEof();
    return 0;
}
