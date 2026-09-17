#include "testlib.h"
using namespace std;
 
int main(int argc, char* argv[])
{
    registerTestlibCmd(argc, argv);
    string lastToken;
    while ( !ouf.seekEof() )
	    lastToken = ouf.readToken();
	quitf( _ok , "Excellent, correct answer using at most %s quries", lastToken.c_str());
    return 0;
}