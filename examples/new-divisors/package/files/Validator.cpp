#include <bits/stdc++.h>
#include "testlib.h"
using namespace std;

int main(int argc, char *argv[]) {
    registerValidation(argc, argv);
    int Testcases = inf.readInt(1,50,"T");
    inf.readEoln();
    for(int t = 1; t <= Testcases; t++) {
        setTestCase(t);
        for(int k = 0; k <= 1; k++){
            int n = inf.readInt(0,332,"n");
            inf.readEoln();
            int last = 0;
            long double LIMIT = 1e100;
            long double prod = 1;
            for(int i = 1; i <= n; i++){
                int p = inf.readInt(last + 1,1'000'000'000,"p[i]");
                inf.readSpace();
                long long e = inf.readLong(1,1'000'000'000'000'000'000,"e[i]");
                inf.readEoln();
                prod *= (long double)e;
                ensuref(prod <= LIMIT , "real a or b is > 1e100");
                ensuref(last < p , "p[] is not increasing");
                last = p;
            } 
        }
    }
    inf.readEof();
}