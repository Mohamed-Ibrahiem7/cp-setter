#include "testlib.h"

using namespace std;

int main(int argc, char* argv[]) {
    registerValidation(argc, argv);

    int T = inf.readInt(1, 1'000, "T");
    inf.readEoln(); 

    for (int tc = 1; tc <= T; tc++) {
        setTestCase(tc);
        long long t1 = inf.readLong(1LL, 1'000'000'000LL, "t1_" + to_string(tc));
        
        inf.readSpace();
        
        long long t2 = inf.readLong(1LL, 1'000'000'000LL, "t2_" + to_string(tc));
        
        ensuref(t1 < t2, "Testcase %d: t1 (%lld) must be strictly less than t2 (%lld)", tc, t1, t2);
        
        inf.readEoln();
    }

    inf.readEof();

    return 0;
}