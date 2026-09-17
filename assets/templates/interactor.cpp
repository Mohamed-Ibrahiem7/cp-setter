#include "testlib.h"

#include <string>

using namespace std;

using ll = long long;

static const int MAX_Q = 0;          // derive this; it must kill the worse approach
static const ll MAX_V = 0;           // upper bound on a queried value

namespace {

// Never quit while the contestant is blocked on a read: send the sentinel first,
// or the verdict becomes "Idleness limit exceeded" and tells them nothing.
[[noreturn]] void reject(TResult verdict, const string& message) {
    cout << "-1" << endl;            // the sentinel, documented in the statement
    quit(verdict, message);
}

ll readParticipantLong(const string& name) {
    if (ouf.seekEof())
        reject(_pe, "Unexpected EOF while reading " + name);
    return ouf.readLong();
}

}  // namespace

int main(int argc, char* argv[]) {
    setName("Interactor for <ProblemName>");
    registerInteraction(argc, argv);

    const int testCases = inf.readInt(1, 1000, "t");
    cout << testCases << endl;

    for (int tc = 1; tc <= testCases; ++tc) {
        setTestCase(tc);

        // Read this case's hidden data from inf. ensuref is correct here -- a broken
        // test file really is the jury's fault.
        const ll hidden = inf.readLong(1, MAX_V, "hidden");
        ensuref(hidden >= 1, "Invalid test data");

        int queries = 0;

        while (true) {
            if (ouf.seekEof())
                reject(_pe, "Unexpected EOF from participant");

            const string operation = ouf.readToken();

            if (operation == "?") {
                if (++queries > MAX_Q)
                    reject(_wa, "Query limit exceeded (" + to_string(queries) +
                                    " > " + to_string(MAX_Q) + ")");

                const ll v = readParticipantLong("query value");
                if (v < 1 || v > MAX_V)
                    reject(_wa, "Queried value is outside the allowed range");

                cout << /* the answer to the query */ 0 << endl;
                continue;
            }

            if (operation == "!") {
                const ll answer = readParticipantLong("answer");
                if (answer != hidden)
                    reject(_wa, "Wrong answer. Expected " + to_string(hidden) +
                                    ", found " + to_string(answer));
                break;
            }

            reject(_pe, "Unexpected token '" + operation + "'");
        }
    }

    if (!ouf.seekEof())
        quitf(_pe, "Extra output after the final answer");

    tout << "OK" << endl;
    quitf(_ok, "All test cases passed");
}
