#include "testlib.h"
#include <vector>

using namespace std;

int main(int argc, char* argv[]) {
    registerGen(argc, argv, 1);
    
    // Usage: gen [T] [MAX_N] [MAX_C] [MAX_V] [MODE]
    // MODE 0: Random
    // MODE 1: Lots of 1-sheets (Amr sweeps)
    // MODE 2: All sheets are 2 (Immediate alternating suicide chain)
    // MODE 3: Force EVEN safe hits (Amr suicides first)
    // MODE 4: Force ODD safe hits (Zezo suicides first)
    
    int T = atoi(argv[1]);
    int MAX_N = atoi(argv[2]);
    long long MAX_C = atoll(argv[3]);
    long long MAX_V = atoll(argv[4]);
    int MODE = atoi(argv[5]);
    
    println(T);
    
    int remaining_n = MAX_N;
    
    for (int t = 1; t <= T; t++) {
        int n = (t == T) ? remaining_n : rnd.next(1, min(remaining_n - (T - t), MAX_N / T * 2));
        remaining_n -= n;
        println(n);
        
        vector<long long> c(n);
        vector<long long> v(n);
        long long safe_moves = 0;
        
        for (int i = 0; i < n; i++) {
            if (MODE == 1) {
                c[i] = (rnd.next(1, 10) <= 7) ? 1 : rnd.next(2LL, MAX_C);
            } else if (MODE == 2) {
                c[i] = 2;
            } else {
                c[i] = rnd.next(1LL, MAX_C);
            }
            if (c[i] >= 2) safe_moves += (c[i] - 2);
        }
        
        // Adjust parity for modes 3 and 4
        if (MODE == 3 && safe_moves % 2 != 0) {
            for (int i = 0; i < n; i++) {
                if (c[i] >= 2 && c[i] < MAX_C) { c[i]++; break; }
                else if (c[i] >= 3) { c[i]--; break; }
            }
        } else if (MODE == 4 && safe_moves % 2 == 0) {
            for (int i = 0; i < n; i++) {
                if (c[i] >= 2 && c[i] < MAX_C) { c[i]++; break; }
                else if (c[i] >= 3) { c[i]--; break; }
            }
        }
        
        for (int i = 0; i < n; i++) {
            v[i] = rnd.next(1LL, MAX_V);
        }
        
        println(c);
        println(v);
    }
    
    return 0;
}