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

void generate(int n, int l, int r){
    cout << n << endl;
    vector< pair< int , long long > > v(n);
    set< int > st;
    for(auto &[i, e] : v){
        do{
            i = rnd.next(l, r);
        } while(st.find(i) != st.end());
        st.insert(i);
        e = rnd.next(1ll, (long long)1e15);
    }
    sort(v.begin(), v.end());
    for(auto &[i, e] : v){
        cout << i << ' ' << e << endl;
    }
}

int main(int argc, char *argv[]) {
    registerGen(argc, argv, 1);
    int id = atoi(argv[1]);
    vector< long long > qp = {1ll, (long long)1e9, (long long)1e9 / 2};
    vector< long long > qe = {(long long)1e18, (long long)1e9 + 7, (long long)1e9 + 8, 1ll};
    vector< pair< long long , long long > > comb;
    for(int i = 0; i < qp.size(); i++){
        for(int j = 0; j < qe.size(); j++){
            comb.push_back({qp[i], qe[j]});
        }
    }
    int m = comb.size();
    int tot = m * m;
    int div = 50;
    int cur = 0;
    int l = id * div;
    int r = min(tot - 1, div * (id + 1) - 1);
    cout << r - l + 1 << endl;
    for(auto &[pa, ea] : comb){
        for(auto &[pb, eb] : comb){
            if(cur <= r && cur >= l){
                cout << 1 << endl;
                cout << pa << ' ' << ea << endl;
                cout << 1 << endl;
                cout << pb << ' ' << eb << endl;
            }
            cur++;
        }
    }
    return 0;
}
