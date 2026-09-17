#include "testlib.h"
#include <vector>
#include <iostream>
#include <algorithm>

using namespace std;

int main(int argc, char* argv[]) {
    registerGen(argc, argv, 1);

    // Usage: gen <mode> <n> <k> <min_val> <max_val> [extra_args]
    string mode = opt<string>(1);
    int n = opt<int>(2);
    int k = opt<int>(3);
    long long min_val = opt<long long>(4);
    long long max_val = opt<long long>(5);

    vector<long long> a;

    if (mode == "random") {
        for (int i = 0; i < n; ++i)
            a.push_back(rnd.next(min_val, max_val));
    }
    else if (mode == "alternating") {
        // Generates + - + - + -
        // Good for stressing the "number of operations" limit
        for (int i = 0; i < n; ++i) {
            long long val = rnd.next(abs(min_val), abs(max_val));
            if (i % 2 == 1) val = -val;
            a.push_back(val);
        }
    }
    else if (mode == "blocks") {
        // Generates blocks of positives and negatives.
        // Example: [10, 10, 10] [-5, -5] [20, 20] ...
        // Forces logic to decide which negative gaps to bridge.
        int i = 0;
        int block_type = rnd.next(0, 1); // 0 for neg, 1 for pos
        while (i < n) {
            int len = rnd.next(1, max(1, n / 20)); // Random block length
            len = min(len, n - i);
            
            // Choose values for this block
            for (int j = 0; j < len; ++j) {
                long long val;
                if (block_type == 0) {
                    // Negative block
                    val = rnd.next(min_val, -1LL); 
                    // Safety if min_val is positive (unlikely but good practice)
                    if (val > 0) val = -val;
                } else {
                    // Positive block
                    val = rnd.next(1LL, max_val);
                }
                a.push_back(val);
            }
            i += len;
            block_type = 1 - block_type; // Switch sign
        }
    }
    else if (mode == "huge_gap") {
        // Positives are huge, Negatives are huge.
        // Tests overflow and high-stakes decisions.
        for (int i = 0; i < n; ++i) {
            if (rnd.next(0, 2) == 0) // 33% chance of negative
                a.push_back(rnd.next(min_val, min_val / 2)); // Very small negatives
            else
                a.push_back(rnd.next(max_val / 2, max_val)); // Very large positives
        }
    }
    else if (mode == "all_neg") {
        // Edge case: Max subarray sum should be the single max element (or 0 if empty allowed)
        // Or flipping a subarray to make it positive.
        for (int i = 0; i < n; ++i) {
             long long val = rnd.next(min_val, -1LL);
             a.push_back(val);
        }
    }
    else if (mode == "one_huge") {
        // Mostly noise, but one massive positive number and one massive negative number
        for (int i = 0; i < n; ++i) a.push_back(rnd.next(-100, 100));
        int idx1 = rnd.next(0, n-1);
        int idx2 = rnd.next(0, n-1);
        a[idx1] = max_val;
        a[idx2] = min_val;
    }

    // Output formatting
    cout << n << " " << k << "\n";
    for (int i = 0; i < n; ++i) {
        cout << a[i] << (i == n - 1 ? "" : " ");
    }
    cout << "\n";

    return 0;
}