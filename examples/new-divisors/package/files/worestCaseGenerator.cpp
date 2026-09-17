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

const int lim = 1e9;

void generateAllAtBegin(){
    int n = 332;
    cout << n << endl;
    for(int i = 1; i <= n; i++){
        cout << i << " 1" << endl;
    }
}

void generateAllAtEnd(){
    int n = 332;
    cout << n << endl;
    for(int i = 1; i <= n; i++){
        cout << lim - n + i << " 1" << endl;
    }
}

void generateAllAtMid(){
    int n = 332;
    cout << n << endl;
    int start = rnd.next(lim / 3, 2 * lim / 3);
    for(int i = 1; i <= n; i++){
        cout << start++ << " 1" << endl;
    }
}


void generateSpread(){
    int n = 332;
    cout << n << endl;
    const int step = lim / n;
    for(int i = 0; i < n; i++){
        cout << 1 + i * step << " 1" << endl;
    }
}

void generateRandom(){
    int n = 332;
    cout << n << endl;
    const int step = lim / n;
    int cur = 1;
    for(int i = 0; i < n; i++){
        cout << cur << " 1" << endl;
        cur += rnd.next(1, step);
    }
}

int main(int argc, char *argv[]) {
    registerGen(argc, argv, 1);
    int t = atoi(argv[1]);
    cout << t << endl;
    int option = 0;
    while(t--){
        option++;
        if (option == 1) {
            generateRandom(); generateAllAtBegin();
        } else if (option == 2) {
            generateAllAtBegin(); generateRandom();
        } else if (option == 3) {
            generateRandom(); generateSpread();
        } else if (option == 4) {
            generateSpread(); generateRandom();
        } else if (option == 5) {
            generateRandom(); generateAllAtEnd();
        } else if (option == 6) {
            generateAllAtEnd(); generateRandom();
        } else if (option == 7) {
            generateRandom(); generateAllAtMid();
        } else if (option == 8) {
            generateAllAtMid(); generateRandom();
        } else if (option == 9) {
            generateAllAtBegin(); generateSpread();
        } else if (option == 10) {
            generateSpread(); generateAllAtBegin();
        } else if (option == 11) {
            generateAllAtBegin(); generateAllAtEnd();
        } else if (option == 12) {
            generateAllAtEnd(); generateAllAtBegin();
        } else if (option == 13) {
            generateAllAtBegin(); generateAllAtMid();
        } else if (option == 14) {
            generateAllAtMid(); generateAllAtBegin();
        } else if (option == 15) {
            generateSpread(); generateAllAtEnd();
        } else if (option == 16) {
            generateAllAtEnd(); generateSpread();
        } else if (option == 17) {
            generateSpread(); generateAllAtMid();
        } else if (option == 18) {
            generateAllAtMid(); generateSpread();
        } else if (option == 19) {
            generateAllAtEnd(); generateAllAtMid();
        } else if (option == 20) {
            generateAllAtMid(); generateAllAtEnd();
        } else {
            option = 1;
            t++;
        }
    }
    return 0;
}
