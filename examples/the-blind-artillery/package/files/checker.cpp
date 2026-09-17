#include "testlib.h"

#include <string>

using namespace std;

int main(int argc, char* argv[]) {
    registerTestlibCmd(argc, argv);
    setTestCase(1);

    if (ouf.seekEof()) {
        quitf(_wa, "Interactor did not accept the submission.");
    }

    const string verdict = ouf.readToken();
    if (verdict != "OK") {
        quitf(_wa, "Invalid interactor result.");
    }

    if (!ouf.seekEof()) {
        quitf(_wa, "Unexpected data after the interactor result.");
    }
    quitf(_ok, "Accepted by interactor.");
}
