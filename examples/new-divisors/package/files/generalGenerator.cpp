#include "testlib.h"
using namespace std;

// Uncomment to use it locally
/*
struct Random{
    long long next(long long l, long long r) {
        random_device rd;
        mt19937 gen(rd());
        uniform_int_distribution<long long> distr(l , r);
        return distr(gen);
    }
};
Random rnd;
*/

class FolkaGenerator{
public:
    void printVector(auto myVec)
    {
        for(int i = 0; i < (int)myVec.size(); i++)
        {
            cout << myVec[i];
            if(i + 1 < (int)myVec.size())
            {
                cout << ' ';
            }
        }
    }
    vector< long long > generateVector(int sizeOfVector, long long elementLowerBound, long long elementUpperBound, bool printTheSample)
    {
        vector< long long > sample(sizeOfVector);
        for(int i = 0; i < sizeOfVector; i++)
        {
            sample[i] = rnd.next(elementLowerBound , elementUpperBound);
        }
        if(printTheSample)
        {
            printVector(sample);
        }
        return sample;
    }
    vector< int > generatePermutationVector(int sizeOfVector, bool printTheSample)
    {
        vector< int > sample(sizeOfVector);
        vector< pair< int , int > > tmp(sizeOfVector);
        for(int i = 0; i < sizeOfVector; i++)
        {
            tmp[i].first = rnd.next(0 , (int)1e9);
            tmp[i].second = i + 1;
        }
        sort(tmp.begin() , tmp.end());
        for(int i = 0; i < sizeOfVector; i++)
        {
            sample[i] = tmp[i].second;
        }
        if(printTheSample)
        {
            printVector(sample);
        }
        return sample;
    }
    vector< vector< int > > generateUnweightedTree(int numberOfNodes , bool printTheSample)
    {
        vector< vector< int > > sample(numberOfNodes + 1);
        for(int x = 2; x <= numberOfNodes; x++)
        {
            int y = rnd.next(1 , x - 1);
            if(printTheSample)
            {
                cout << x << ' ' << y << endl;
            }
            sample[x].push_back(y);
        }
        return sample;
    }
    vector< vector< pair< int , long long > > > generateWeightedTree(int numberOfNodes, long long weightLowerBound, long long weightUpperBound, bool printTheSample)
    {
        vector< vector< pair< int , long long > > > sample(numberOfNodes + 1);
        for(int x = 2; x <= numberOfNodes; x++)
        {
            int y = rnd.next(1 , x - 1);
            long long w = rnd.next(weightLowerBound , weightUpperBound);
            if(printTheSample)
            {
                cout << x << ' ' << y << ' ' << w << endl;
            }
            sample[x].push_back({ y , w });
        }
        return sample;
    }
    vector< vector< pair< int , long long > > > generateLinerWeightedTree(int numberOfNodes, long long weightLowerBound, long long weightUpperBound, bool printTheSample)
    {
        vector< vector< pair< int , long long > > > sample(numberOfNodes + 1);
        for(int x = 2; x <= numberOfNodes; x++)
        {
            int y = x - 1;
            long long w = rnd.next(weightLowerBound , weightUpperBound);
            if(printTheSample)
            {
                cout << x << ' ' << y << ' ' << w << endl;
            }
            sample[x].push_back({ y , w });
        }
        return sample;
    }
};
FolkaGenerator folka;
const long long maxLimit = 1e18;


long double logBaseK(long double n, long double k) {
    return log(n) / log(k);
}
const long long getLimit(int n){
    long long l = 2, r = maxLimit;
    long long res = 1;
    while(l <= r){
        long long mid = l + r >> 1;
        if(100 * logBaseK(10, mid) >= n){
            res = mid - 1;
            l = ++mid;
        }
        else{
            r = --mid;
        }
    }
    return res;
}

set< int > both;

void generate(int n, int l, int r){
    const long long lim = getLimit(n);
    cout << n << endl;
    vector< pair< int , long long > > v;
    set< int > st = both;
    while(st.size() < n){
        int i = rnd.next(l, r);
        st.insert(i);
    }
    for(auto &i : st){
        v.push_back({i, rnd.next(1ll, lim)});
    }
    sort(v.begin(), v.end());
    for(auto &[i, e] : v){
        cout << i << ' ' << e << endl;
    }
}

int main(int argc, char *argv[]) {
    registerGen(argc, argv, 1);
    int t = atoi(argv[1]);
    int lnA = atoi(argv[2]);
    int rnA = atoi(argv[3]);
    int lA = atoi(argv[4]);
    int rA = atoi(argv[5]);
    int lnB = atoi(argv[6]);
    int rnB = atoi(argv[7]);
    int lB = atoi(argv[8]);
    int rB = atoi(argv[9]);
    cout << t << endl;
    while(t--) {
        both.clear();
        int n = rnd.next(lnA, rnA);
        int m = rnd.next(lnB, rnB);
        int common = rnd.next(0, min(n, m));
        while(both.size() < common){
            both.insert(rnd.next(max(lA, lB), min(rA, rB)));
        }
        generate(n, lA, rA);
        generate(m, lB, rB);
    }
    return 0;
}
