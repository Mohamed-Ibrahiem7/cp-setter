#include "testlib.h"

#include <string>

using namespace std;

// The checker for an interactive problem reads what the INTERACTOR wrote to tout,
// which Polygon hands it as ouf. It does not see the contestant's stream.
//
// Keep it this small. The interactor already decided; this only confirms that the
// interactor reached its success path, so that a crashed or killed interactor can
// never be mistaken for an accepted submission.

int main(int argc, char* argv[]) {
    registerTestlibCmd(argc, argv);
    setTestCase(1);

    if (ouf.seekEof())
        quitf(_wa, "Interactor did not accept the submission.");

    const string verdict = ouf.readToken();
    if (verdict != "OK")
        quitf(_wa, "Invalid interactor result.");

    if (!ouf.seekEof())
        quitf(_wa, "Unexpected data after the interactor result.");

    quitf(_ok, "Accepted by interactor.");
}
