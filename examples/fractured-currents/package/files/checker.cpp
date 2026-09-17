#include "testlib.h"
#include <bits/stdc++.h>
using namespace std;

typedef long long ll;

const int MOD = 1000000007;

int main(int argc, char* argv[]) {
    registerTestlibCmd(argc, argv);

    ll ja = ans.readLong();
    ll pa = ouf.readLong();

    ja %= MOD;
    if (ja < 0) ja += MOD;
    pa %= MOD;
    if (pa < 0) pa += MOD;

    if (ja != pa) {
        quitf(_wa, "expected %lld, found %lld", ja, pa);
    }

    quitf(_ok, "ok");
}
