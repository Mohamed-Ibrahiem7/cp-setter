#include "testlib.h"

#include <iostream>
#include <string>

using namespace std;

using ll = long long;

static const int MAX_Q = 80;
static const ll MAX_T = 1'000'000'000LL;

namespace {

[[noreturn]] void reject(TResult verdict, const string& message) {
    cout << "-2 -2" << endl;
    quit(verdict, message);
}

ll readParticipantLong(const string& name) {
    if (ouf.seekEof()) {
        reject(_pe, "Unexpected EOF while reading " + name);
    }

    return ouf.readLong();
}

}  // namespace

int main(int argc, char* argv[]) {
    setName("Interactor for Artillery Cannon");
    registerInteraction(argc, argv);

    const int testCases = inf.readInt(1, 1'000, "T");
    cout << testCases << endl;

    for (int tc = 1; tc <= testCases; ++tc) {
        setTestCase(tc);

        const ll t1 = inf.readLong(1, MAX_T, "t1");
        const ll t2 = inf.readLong(1, MAX_T, "t2");
        ensuref(t1 < t2, "Invalid test data: t1 must be less than t2");

        int queries = 0;

        while (true) {
            if (ouf.seekEof()) {
                reject(_pe, "Unexpected EOF from participant");
            }

            const string operation = ouf.readToken();

            if (operation == "?") {
                if (++queries > MAX_Q) {
                    reject(_wa, "Query limit exceeded (" + to_string(queries) +
                                    " > " + to_string(MAX_Q) + ")");
                }

                const ll t = readParticipantLong("queried timestamp");
                if (t < 1 || t > MAX_T) {
                    reject(_wa, "Queried timestamp is outside [1, 10^9]");
                }

                const int position =
                    (t == t1 || t == t2) ? 0 : (t1 < t && t < t2 ? 1 : -1);

                const ll twiceTime = 2 * t;
                const ll rootSum = t1 + t2;
                const int direction =
                    twiceTime < rootSum ? 1 : (twiceTime > rootSum ? -1 : 0);

                cout << position << ' ' << direction << endl;
                continue;
            }

            if (operation == "!") {
                const ll answer1 = readParticipantLong("answer t1");
                const ll answer2 = readParticipantLong("answer t2");

                if (answer1 != t1 || answer2 != t2) {
                    reject(_wa, "Wrong answer. Expected (" + to_string(t1) + ", " +
                                    to_string(t2) + "), found (" + to_string(answer1) +
                                    ", " + to_string(answer2) + ")");
                }

                break;
            }

            reject(_pe, "Unexpected token '" + operation + "'");
        }
    }

    if (!ouf.seekEof()) {
        quitf(_pe, "Extra output after the final answer");
    }
    tout << "OK" << endl;
    quitf(_ok, "All test cases passed");
}
