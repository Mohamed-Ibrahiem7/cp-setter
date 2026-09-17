#include <bits/stdc++.h>
#include "testlib.h"
 
using namespace std;
 
int main(int argc, char* argv[])
{
	registerTestlibCmd(argc, argv);
	 string qq=ouf.readToken();
	 string xx=ouf.readToken();
	 int q=stoi(qq);
	 int x=stoi(xx);
	 int n = inf.readInt(1, 1000000000, "N");

     if(q>30)
    	quitf(_wa, "The number of queries=%d > 30",q);
    else if(n!=x)
            quitf(_wa, "The number not correct expected %d but found %d",n,x);
    else if(x==-1)
    	quitf(_wa, "print empty or the number not valid");
     else 
        quitf(_ok, "OK , Correct");
 
	return 0;
}