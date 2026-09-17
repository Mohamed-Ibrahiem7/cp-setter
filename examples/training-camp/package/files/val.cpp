#include "testlib.h"

using namespace std;

int main(int argc, char* argv[]) {
    registerValidation(argc, argv);
    
    int t = inf.readInt(1, 10000, "T");
    inf.readEoln();
    
    int sum_n = 0;
    for (int i = 1; i <= t; i++) {
        int n = inf.readInt(1, 200000, "N");
        inf.readEoln();
        
        sum_n += n;
        ensuref(sum_n <= 200000, "Sum of N over test cases exceeds 200000");
        
        for (int j = 0; j < n; j++) {
            inf.readInt(1, 1000000000, "C_i");
            if (j < n - 1) inf.readSpace();
        }
        inf.readEoln();
        
        for (int j = 0; j < n; j++) {
            inf.readInt(1, 1000000000, "V_i");
            if (j < n - 1) inf.readSpace();
        }
        inf.readEoln();
    }
    
    inf.readEof();
    return 0;
}