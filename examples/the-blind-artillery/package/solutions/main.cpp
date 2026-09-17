// Author : AhmedQassem_
#include <bits/stdc++.h>
using namespace std;
using ll = long long;
using ld = long double;
using ull = unsigned long long;

//#define endl '\n'
#define int ll
#define ep cout << fixed << setprecision(12)
#define all(x) (x).begin(), (x).end()
#define allr(x) (x).rbegin(), (x).rend()

const int INF = 0x3f3f3f3f;
const ll LINF = 0x3f3f3f3f3f3f3f3f;
const int mod = 1e9 + 7;
//const int mod = 998244353;
const ld PI = acosl(-1.0L);
int dx[] = {0,0,1,-1};
int dy[] = {1,-1,0,0};

int gcd(int a, int b) { return b ? gcd(b, a % b) : a; }
int lcm(int a, int b) { return a / gcd(a, b) * b; }

void fileio() {

}

void fastio() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cout.tie(nullptr);
}

const int N = 2e5+5, M = 23;

pair<int, int> query(int t) {
    cout << "? " << t << endl;
    int p, d;
    cin >> p >> d;
    
    if(p == -2 && d == -2) exit(0);    
    return {p, d};
}

void Magek() {
    int t1 = -1, t2 = -1;

    int L = 1, R = 1e9;
    while (L <= R) {
        int mid = L + (R - L) / 2;
        pair<int, int> res = query(mid);
        int p = res.first;
        int d = res.second;

        if (p == 0 && d == 1) {
            t1 = mid;
            break;
        } else if (p == -1 && d == 1) {
            L = mid + 1; 
        } else {
            R = mid - 1; 
        }
    }

    L = t1 + 1; 
    R = 1e9;
    while (L <= R) {
        int mid = L + (R - L) / 2;
        pair<int, int> res = query(mid);
        int p = res.first;
        int d = res.second;

        if (p == 0 && d == -1) {
            t2 = mid;
            break;
        } else if (p == -1 && d == -1) {
            R = mid - 1; 
        } else {
            L = mid + 1; 
        }
    }

    cout << "! " << t1 << " " << t2 << endl;
}

int32_t main() {
    //fileio();
    fastio();
    int t = 1;
    cin >> t;
    while (t--) Magek();
    return 0;
}