#include "testlib.h"
#include <iostream>

using namespace std;

int main(int argc, char* argv[]) {
    registerGen(argc, argv, 1);
    
    int max_t = rnd.next(1, 2);
    int T = (max_t == 1 ? 1000 : rnd.next(1, 1000)); 
    
    int type = rnd.next(1, 5); 

    cout << T << endl;

    for (int tc = 1; tc <= T; tc++) {
        long long t1, t2;

        if (type == 1) {
            t1 = rnd.next(1LL, 100LL);
            t2 = rnd.next(t1 + 1, 200LL);
        } 
        else if (type == 2) {
            t1 = rnd.next(1LL, 999999999LL);
            t2 = t1 + rnd.next(1LL, 5LL);
            if (t2 > 1000000000LL) t2 = 1000000000LL;
            if (t1 == t2) t1--; 
        } 
        else if (type == 3) {
            t1 = rnd.next(1LL, 100LL);
            t2 = rnd.next(999999000LL, 1000000000LL);
        } 
        else if (type == 4) {
            t1 = rnd.next(500000000LL, 999999999LL);
            t2 = rnd.next(t1 + 1, 1000000000LL);
        }
        else {
            t1 = rnd.next(1LL, 999999999LL);
            t2 = rnd.next(t1 + 1, 1000000000LL);
        }

        cout << t1 << " " << t2 << endl;
    }

    return 0;
}