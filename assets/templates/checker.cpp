#include "testlib.h"
#include <bits/stdc++.h>

using namespace std;

// Custom checker skeleton for problems where several outputs are valid.
//
// Shape of the job, per test case:
//   1. read the input for this case from inf
//   2. read the jury answer from ans and the participant answer from ouf
//   3. check the participant answer is well formed and legal for this input
//   4. compare its QUALITY to the jury's, never its SHAPE
//
// Comparing shapes rejects correct answers; skipping step 3 or the optimality
// half of step 4 accepts wrong ones. Both halves are required.

const long long ANS_MAX = 4000000000000000000LL;

int main(int argc, char *argv[]) {
    registerTestlibCmd(argc, argv);

    int t = inf.readInt();
    for (int tc = 1; tc <= t; tc++) {
        setTestCase(tc);

        int n = inf.readInt();
        vector<int> a(n);
        for (int i = 0; i < n; i++)
            a[i] = inf.readInt();

        long long juryScore = ans.readLong(-ANS_MAX, ANS_MAX, "jury answer");
        long long partScore = ouf.readLong(-ANS_MAX, ANS_MAX, "participant answer");

        // TODO: read the participant's witness/construction and verify it is legal
        //       for this input, and that it really achieves partScore.
        //       quitf(_wa, "...") on anything illegal.

        if (partScore > juryScore)
            quitf(_fail, "participant answer %lld beats jury answer %lld",
                  partScore, juryScore);
        if (partScore < juryScore)
            quitf(_wa, "participant answer %lld is worse than jury answer %lld",
                  partScore, juryScore);
    }

    if (!ouf.seekEof())
        quitf(_wa, "extra output after the last test case");

    quitf(_ok, "%d test cases correct", t);
}
