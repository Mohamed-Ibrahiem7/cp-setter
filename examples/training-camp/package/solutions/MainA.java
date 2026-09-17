import java.io.*;
import java.util.*;

public class MainA {
    static void solve(FastScanner fs, StringBuilder out) throws Exception {
        int n = fs.nextInt();

        long[] c = new long[n];
        long[] v = new long[n];

        for (int i = 0; i < n; i++)
            c[i] = fs.nextLong();

        for (int i = 0; i < n; i++)
            v[i] = fs.nextLong();

        long ans = 0;
        long moves = 0;

        ArrayList<Long> prizes = new ArrayList<>();

        for (int i = 0; i < n; i++) {
            if (c[i] == 1) {
                ans += v[i];
            } else {
                moves += c[i] - 1;
                prizes.add(v[i]);
            }
        }

        prizes.sort(Collections.reverseOrder());

        int start = (int) (moves & 1L);

        for (int i = start; i < prizes.size(); i += 2)
            ans += prizes.get(i);

        out.append(ans).append('\n');
    }

    public static void main(String[] args) throws Exception {
        FastScanner fs = new FastScanner(System.in);
        StringBuilder out = new StringBuilder();

        int T = fs.nextInt();

        while (T-- > 0)
            solve(fs, out);

        System.out.print(out);
    }

    static class FastScanner {
        private final InputStream in;
        private final byte[] buffer = new byte[1 << 16];
        private int ptr = 0, len = 0;

        FastScanner(InputStream is) {
            in = is;
        }

        private int read() throws IOException {
            if (ptr >= len) {
                len = in.read(buffer);
                ptr = 0;
                if (len <= 0)
                    return -1;
            }
            return buffer[ptr++];
        }

        long nextLong() throws IOException {
            int c;
            do {
                c = read();
            } while (c <= ' ');

            boolean neg = false;
            if (c == '-') {
                neg = true;
                c = read();
            }

            long res = 0;
            while (c > ' ') {
                res = res * 10 + (c - '0');
                c = read();
            }

            return neg ? -res : res;
        }

        int nextInt() throws IOException {
            return (int) nextLong();
        }
    }
}