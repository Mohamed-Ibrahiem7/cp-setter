#include "testlib.h"
#include <bits/stdc++.h>
using namespace std;

class State{
private:
    const int _WA = -1;
    const int _AC = 1;
    const int _inQ = 0;
    int now = _inQ;
public:
    void asking() {
        now = _inQ;
    }
    bool isAsking() {
        return (now == _inQ);
    }

    void accepted() {
        now = _AC;
    }
    bool isAccepted() {
        return (now == _AC);
    }

    void wrong() {
        now = _WA;
    } 
    bool isWrong() {
        return (now == _WA);
    }
};

class Solution {
private:
    long long single[2];
    long long ans;
    int n[2];
    vector< long long > idx[2];
    vector< long long > pref[2];
    
public:
    Solution(){

    }
    bool isRelativelyCorrect(Solution other) {
        if(ans != other.ans){
            quitf(_wa, "Not a correct answer expected %d found %d", ans, other.ans);
        }
        return ans == other.ans;
    }
    void readSolution(auto &in){
        ans = in.readInt(0, int(1e9 + 6), "Number of divisors of A * B");
    }
    void readTest(auto &in){
        for(int k = 0; k <= 1; k++){
            n[k] = in.readInt(0, int(333), "n");
            idx[k] = pref[k] = vector< long long > (n[k] + 1, 0);
            for(int i = 1; i <= n[k]; i++){
                idx[k][i] = in.readInt(1, (int)1e9, "idx[i]");
                pref[k][i] = in.readLong(1ll, (long long)1e18, "e[i]");
                pref[k][i] += pref[k][i - 1];
            }
        }
        
    }
    void generateCorrectSolution(){
        map< long long , long long > mp;
        for(int k = 0; k <= 1; k++){
            for(int i = 1; i <= n[k]; i++){
                mp[idx[k][i]] += pref[k][i] - pref[k][i - 1];
            }
        }
        const int mod = 1e9 + 7;
        ans = 1;
        
        for(auto &[p, e] : mp){
            ans = (ans * ((e + 1) % mod)) % mod;
        }
        for(int k = 0; k <= 1; k++){
            single[k] = 1;
            for(int i = 1; i <= n[k]; i++){
                long long e = pref[k][i] - pref[k][i - 1];
                single[k] = (single[k] * ((e + 1) % mod)) % mod;
            }
        }
        // ostringstream oss;
        // for (auto [k, v] : mp) {
        //     oss << v;
        //     oss << ' ';
        // }
        // oss << ans << ' ';
        // oss << single[0] << ' ';
        // oss << single[1] << ' ';
        // string s = oss.str();
        // quitf(_wa, "Tracing: Vector contents: %s", s.c_str());
    }
    long long query(int k, int i){
        int it = upper_bound(idx[k].begin(), idx[k].end(), i) - idx[k].begin();
        return pref[k][it - 1];
    }
    long long getPrint(int j){
        return single[j];
    }
};

class SolutionTracing{
private:
    int Q1Limit;
    int Q1Count;
    int n;
    Solution guess;
public:
    State state;
    SolutionTracing(){
        Q1Count = 0;
        Q1Limit = 8500;
        guess = Solution();
    }
    bool isLimit(){
        return (Q1Count > Q1Limit);
    }
    Solution getSolution(){
        return guess;
    }
    void readAnswer(auto &in){
        guess.readSolution(in);
    }
    void increaseQ1(){
        Q1Count++;
    }
    int getTakenQueies(){
        return Q1Count;
    }
};

class HiddenAnswer{
private:
    int n;
    Solution ans;
public:

    HiddenAnswer(){
        
    }
    void readAnswer(){
        ans.readTest(inf);
        ans.generateCorrectSolution();
    }
    bool correctAnswer(SolutionTracing &other){
        return (ans.isRelativelyCorrect(other.getSolution()));
    }
    void answerQ1(auto &in){
        in.readSpace();
        char c = in.readChar();
        ensuref(c == 'A' || c == 'B' , "input character must be A or B, but got '%c'", c);
        int i = in.readInt(1, int(1e9), "input index i is out of the range [1,1'000'000'000]");
        cout << ans.query(c - 'A', i) << endl;
    }
    Solution getSolution(){
        return ans;
    }
};


const bool isTestcases = true;
const int testCasesLimit = 50; // useless if there is no testcases.

bool run(SolutionTracing &Ans, HiddenAnswer &Hans, auto &in){
    Ans.state.asking();
    while(Ans.state.isAsking()){
        string type = in.readToken();
        if(type == "?"){
            Ans.increaseQ1();
            Hans.answerQ1(in);
        }
        else if(type == "!"){
            Ans.readAnswer(in);
            if(Hans.correctAnswer(Ans)){
                Ans.state.accepted();
            }
            else {
                 Ans.state.wrong();
            }
        }
        else {
            quitf(_wa, "Invalid query type '%s'", type.c_str());
        }
        if(Ans.isLimit()) {
            quitf(_wa, "Too much queries");
        }
    }
    return Ans.state.isAccepted();
}

void printTest(HiddenAnswer &Hans){
    cout << Hans.getSolution().getPrint(0) << ' ' << Hans.getSolution().getPrint(1) << endl;
}

int main(int argc, char ** argv){
    registerInteraction(argc, argv);
    int TestCases = 1;
    if(isTestcases) {
        TestCases = inf.readInt(1 , testCasesLimit , "testcases");
        cout << TestCases << endl;
    }

    int testcase = 1;
    bool Accepted = true;
    int maxQueries = 0;
    for(; testcase <= TestCases; testcase++){
        HiddenAnswer Hans;
        Hans.readAnswer();
        printTest(Hans);
        SolutionTracing Pans;
        Accepted &= run(Pans, Hans, ouf);
        maxQueries = max(maxQueries, Pans.getTakenQueies());
        if(!Accepted){
            break;
        }
        
    }


    if(isTestcases){
        if(Accepted){
            tout << maxQueries << endl;
            quitf(_ok, "Excellent %d correct answers!", TestCases - 1);
        }
        else if (!Accepted){
            quitf(_wa, "Not a correct answer on test %d", testcase);
        }
        else{
            quitf(_wa, "Query limit reached and answer not found on test %d", testcase);
        }
    }
    else{
        if(Accepted){
            tout << maxQueries << endl;
            quitf(_ok, "Excellent, correct answer!");
        }
        else if (!Accepted){
            quitf(_wa, "Not a correct answer");
        }
        else{
            quitf(_wa, "Query limit reached and answer not found");
        }
    }

}