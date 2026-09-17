#include "testlib.h"
#include <bits/stdc++.h>
using namespace std;

int main(int argc, char* argv[]) {
    registerTestlibCmd(argc, argv);

    int n = 0;
    while (!ans.seekEof() && !ouf.seekEof()) {
        n++;
        double ja = ans.readDouble();
        double pa = ouf.readDouble();
        if (!doubleCompare(ja, pa, 1e-6)) {
            quitf(_wa, "%d%s numbers differ - expected '%.10f', found '%.10f'",
                  n, englishEnding(n).c_str(), ja, pa);
        }
    }

    if (!ans.seekEof()) {
        quitf(_wa, "answer has extra output");
    }
    if (!ouf.seekEof()) {
        quitf(_wa, "output has extra output");
    }

    quitf(_ok, "%d token(s)", n);
}
