#include "testlib.h"
#include <bits/stdc++.h>
#define MAXW        1000000000
using namespace std;


int main(int argc, char* argv[]) {

    ios_base::sync_with_stdio(0);
    cin.tie(0);
    
    registerGen(argc, argv, 1);
    
    
     long long n=  rnd.next(1, MAXW);
     cout<<n<<endl;
       
    return 0;
}
