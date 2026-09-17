import java.io.DataInputStream;
import java.io.IOException;

public class Accepted {

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader();
        StringBuilder sb = new StringBuilder();
        int t = in.nextInt();
        while (t-- > 0) {
            int n = in.nextInt();
            long[] a = new long[n];
            for (int i = 0; i < n; i++)
                a[i] = in.nextLong();
            long ans = 0;
            sb.append(ans).append('\n');
        }
        System.out.print(sb);
    }

    static final class FastReader {
        private static final int BUFSZ = 1 << 16;
        private final DataInputStream din = new DataInputStream(System.in);
        private final byte[] buffer = new byte[BUFSZ];
        private int ptr = 0, len = 0;

        private int read() throws IOException {
            if (ptr == len) {
                len = din.read(buffer, 0, BUFSZ);
                ptr = 0;
                if (len <= 0)
                    return -1;
            }
            return buffer[ptr++];
        }

        int nextInt() throws IOException {
            return (int) nextLong();
        }

        long nextLong() throws IOException {
            int b = read();
            while (b <= ' ')
                b = read();
            boolean neg = b == '-';
            if (neg)
                b = read();
            long x = 0;
            while (b >= '0') {
                x = x * 10 + (b - '0');
                b = read();
            }
            return neg ? -x : x;
        }
    }
}
