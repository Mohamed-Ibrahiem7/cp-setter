import java.io.*;
import java.util.*;

public class Main {
    static final long MOD = 1_000_000_007;
    static final int INF = (int)1e9;
    static BufferedReader br;
    static PrintWriter out;
    // Use a TreeMap to keep keys sorted
    static TreeMap<Long, Integer> mp = new TreeMap<>();

    static long ask(char t, int i) throws IOException {
        if (i <= 0) return 0;
        out.println("? " + t + " " + i);
        out.flush();
        long x = Long.parseLong(br.readLine().trim());
        if (t == 'A') {
            mp.merge(x, i, Math::min);
        }
        return x;
    }

    static void get(char t, long lval, long rval, int l, int r) throws IOException {
        if (r < l || lval >= rval) return;
        int mid = (l + r) >> 1;
        long val = ask(t, mid);
        // because mp.get(val) is the smallest index at which we saw this val
        int pos = mp.get(val);
        get(t, lval, val, l, pos - 1);
        get(t, val, rval, mid + 1, r);
    }

    public static void main(String[] args) throws IOException {
        br = new BufferedReader(new InputStreamReader(System.in));
        out = new PrintWriter(new OutputStreamWriter(System.out));
        int T = Integer.parseInt(br.readLine().trim());
        while (T-- > 0) {
            StringTokenizer st = new StringTokenizer(br.readLine());
            Mint a = new Mint(Long.parseLong(st.nextToken()));
            Mint b = new Mint(Long.parseLong(st.nextToken()));
            Mint gcd = new Mint(1);

            mp.clear();
            long firstA = ask('A', 1);
            long lastA  = ask('A', INF);
            get('A', firstA, lastA, 1, INF);

            long last = 0;
            for (Map.Entry<Long, Integer> e : mp.entrySet()) {
                long Ainc = e.getKey() - last;
                int  pos  = e.getValue();
                long Binc = ask('B', pos) - ask('B', pos - 1);

                // a *= inv(Ainc + 1), b *= inv(Binc + 1), gcd *= (Ainc + Binc + 1)
                a   = a.mul(new Mint(Mint.modInverse(Ainc + 1)));
                b   = b.mul(new Mint(Mint.modInverse(Binc + 1)));
                gcd = gcd.mul(new Mint(Ainc + Binc + 1));

                last = e.getKey();
            }

            Mint ans = gcd.mul(a).mul(b);
            out.println("! " + ans.value());
            out.flush();
        }
    }

    static class Mint {
        private long v;
        Mint(long _v) { v = ((_v % MOD) + MOD) % MOD; }
        Mint add(Mint o) { return new Mint(v + o.v); }
        Mint mul(Mint o) { return new Mint((v * o.v) % MOD); }
        long value()    { return v; }

        static long modInverse(long x) {
            return pow(x, MOD - 2);
        }
        static long pow(long base, long exp) {
            long res = 1;
            base = (base % MOD + MOD) % MOD;
            while (exp > 0) {
                if ((exp & 1) == 1) res = (res * base) % MOD;
                base = (base * base) % MOD;
                exp >>= 1;
            }
            return res;
        }
    }
}
