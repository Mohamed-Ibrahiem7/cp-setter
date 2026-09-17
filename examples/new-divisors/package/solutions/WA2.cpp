/**
 *    author:  Folka
**/

#include <bits/stdc++.h>
using namespace std;

const int mod = 1e9 + 7;
class Mint {
private:
    int myInt;

    // Modular handler
    Mint add(long long other) { return (myInt % mod + other % mod) % mod; }

    Mint add(Mint other) { return add(other.myInt); }


    Mint product(long long other) { return (myInt % mod) * (other % mod) % mod; }

    Mint product(Mint other) { return product(other.myInt); }


    Mint divide(long long other) { return myInt / other; }

    Mint divide(Mint other) { return divide(other.myInt); }


    void assign(long long other) { myInt = other % mod; }

    void assign(Mint other) { assign(other.myInt); }


    Mint Mod(long long other) { return myInt % other; }

    Mint Mod(Mint other) { return Mod(other.myInt); }


    Mint AND(long long other) { return (myInt & other); }

    Mint AND(Mint other) { return AND(other.myInt); }


    Mint OR(long long other) { return (myInt | (other % mod)) % mod; }

    Mint OR(Mint other) { return OR(other.myInt); }


    Mint XOR(long long other) { return (myInt ^ (other % mod)) % mod; }

    Mint XOR(Mint other) { return XOR(other.myInt); }

public:
    // Operator overloading
    friend std::ostream &operator<<(std::ostream &os, Mint other);

    friend std::istream &operator>>(std::istream &is, Mint other);

    Mint operator-() const { return -myInt; }
    Mint operator+() const { return +myInt; }
    // Overload < operator
    bool operator<(const Mint other) const {
        return myInt < other.myInt;
    }

    bool operator<(long long other) const {
        return myInt < other;
    }

    // Overload > operator
    bool operator>(const Mint other) const {
        return myInt > other.myInt;
    }

    bool operator>(long long other) const {
        return myInt > other;
    }

    // Overload == operator
    bool operator==(const Mint other) const {
        return myInt == other.myInt;
    }

    bool operator==(long long other) const {
        return myInt == other;
    }

    // *** Addition
    Mint operator+(auto other) { return add(other); }

    Mint operator+=(auto other) { return Mint(myInt = add(other)); }

    friend Mint operator+(long long rhs, Mint lhs) { return (rhs % mod + lhs.myInt) % mod; }

    // *** Subtruction
    Mint operator-(auto other) { return add(-other); }

    Mint operator-=(auto other) { return Mint(myInt = add(-other)); }

    friend Mint operator-(long long rhs, Mint lhs) { return (rhs % mod - lhs.myInt) % mod; }

    // *** Product
    Mint operator*(auto other) { return product(other); }

    Mint operator*=(auto other) { return Mint(myInt = product(other)); }

    friend Mint operator*(long long rhs, Mint lhs) { return (rhs % mod * lhs.myInt) % mod; }

    // *** Division
    Mint operator/(auto other) { return divide(other); }

    Mint operator/=(auto other) { return Mint(myInt = divide(other)); }

    friend Mint operator/(long long rhs, Mint lhs) { return (rhs % mod / lhs.myInt) % mod; }

    // *** Modulus
    Mint operator%(auto other) { return Mod(other); }

    Mint operator%=(auto other) { return Mint(myInt = Mod(other)); }

    friend Mint operator%(long long rhs, Mint lhs) { return (rhs % lhs.myInt); }

    // *** Bitwise operators
    Mint operator&(auto other) { return AND(other); }

    Mint operator&=(auto other) { return Mint(myInt = AND(other)); }

    friend Mint operator&(long long rhs, Mint lhs) { return (rhs & lhs.myInt); }

    Mint operator|(auto other) { return OR(other); }

    Mint operator|=(auto other) { return Mint(myInt = OR(other)); }

    friend Mint operator|(long long rhs, Mint lhs) { return ((rhs % mod) | lhs.myInt) % mod; }

    Mint operator^(auto other) { return XOR(other); }

    Mint operator^=(auto other) { return Mint(myInt = XOR(other)); }

    friend Mint operator^(long long rhs, Mint lhs) { return ((rhs % mod) ^ lhs.myInt) % mod; }

    // Constuctor and Destrucotr
    Mint(auto other) {
        assign(other);
    }

    Mint() {
        assign(0);
    }

    int pos() {
        myInt = (0ll + myInt + mod) % mod;
        return myInt;
    }

    operator int() const {
        return myInt;
    }

    operator long long() const {
        return myInt;
    }
};

std::ostream &operator<<(std::ostream &os, Mint other) {
    os << other.myInt;
    return os;
}

class FolkaMath {
private:
public:
    long long power(auto base, auto exponent) {
        Mint bb = base;
        long long ee = exponent;
        long long result = 1;
        while (ee > 0) {
            if (ee % 2 == 1) {
                result = (result * bb) % mod;
            }
            ee /= 2;
            bb *= bb;
        }
        return result;
    }

    long long modInverse(auto base) {
        return power(base, mod - 2);
    }

    long long sum(long long n) {
        return n * (n + 1) / 2;
    }

    long long sum(long long l, long long r) {
        return sum(r) - sum(l - 1);
    }
};

FolkaMath math;
map< long long , int > mp;
const long long inf = 1e9;


long long ask(const char t, int i) {
    if(i <= 0) {
        return 0;
    }
    cout << "? " << t << ' ' << i << endl;
    long long x; cin >> x;
    if('A' == t) {
        if(mp.find(x) == mp.end()) {
            mp[x] = i;
        }
        else {
            mp[x] = min(mp[x], i);
        }
    }
    return x;
}

void get(char t, long long lval, long long rval, int l, int r) {
    if(r < l || lval >= rval) {
        return;
    }
    int mid = l + r >> 1;
    long long val = ask(t, mid);
    get(t, lval, val, l, mp[val] - 1);
    get(t, val, rval, mid + 1, r);
}

int main() {
    std::ios_base::sync_with_stdio(false);
    cin.tie(nullptr);
    cout.tie(nullptr);
    int T = 1;
    cin >> T;
    for (int t = 1; t <= T; t++) {
        int inputA, inputB;
        cin >> inputA >> inputB;
        Mint a(inputA), b(inputB);
        Mint gcd = 1;
        get('A', ask('A', 1), ask('A', inf), 1, inf);
        long long last = 0;
        for(auto &[e, p] : mp){
            long long A = e - last;
            long long B = ask('B', p) - ask('B', p - 1);
            a *= math.modInverse(A + 1);
            b *= math.modInverse(B + 1);
            gcd *= A + B + 1;
            last = e;
        }
        Mint ans = gcd * a * b;
        cout << "! " << ans.pos() << endl;
    }
    return 0;
}