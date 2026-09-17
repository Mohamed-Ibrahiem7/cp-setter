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
map< int , long long > mp[2];
const long long inf = 1e9;

long long ask(const char t, int i) {
    if(i <= 0) {
        return 0;
    }
    if(i > inf) {
        return inf + 1;
    }
    if(mp[t - 'A'].find(i) != mp[t - 'A'].end()) {
        return mp[t - 'A'][i];
    }
    cout << "? " << t << ' ' << i << endl;
    long long x; cin >> x;
    mp[t - 'A'][i] = x;
    return x;
}

int getNext(char t, int i) {
    long long fixed = ask(t, i);
    int l = i + 1, r = inf + 1;
    int ans = l;
    while(l <= r) {
        int mid = (l + r) >> 1;
        if(ask(t, mid) == fixed) {
            ans = mid + 1;
            l = ++mid;
        }
        else {
            r = --mid;
        }
    }
    return ans;
}

int main() {
    std::ios_base::sync_with_stdio(false);
    cin.tie(nullptr);
    cout.tie(nullptr);
    int T = 1;
    cin >> T;
    for (int t = 1; t <= T; t++) {
        mp[0].clear();
        mp[1].clear();
        int inputA, inputB;
        cin >> inputA >> inputB;
        Mint a(inputA), b(inputB);
        Mint gcd = 1;
        int l = 0, r = getNext('A', l);
        while(r <= inf) {
            long long A = ask('A', r) - ask('A', l);
            long long B = ask('B', r) - ask('B', l);
            a *= math.modInverse(A + 1);
            b *= math.modInverse(B + 1);
            gcd *= A + B + 1;
            l = r;
            r = getNext('A', r);
        }
        Mint ans = gcd * a * b;
        cout << "! " << ans.pos() << endl;
    }
    return 0;
}
