import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.io.IOException;
import java.util.StringTokenizer;
import java.util.Random;
import java.util.Arrays;

public class Solution {
    // Fast I/O helper class
    static class FastScanner {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        StringTokenizer st = new StringTokenizer("");

        String next() {
            while (!st.hasMoreTokens()) {
                try {
                    String line = br.readLine();
                    if (line == null) return null;
                    st = new StringTokenizer(line);
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
            return st.nextToken();
        }

        int nextInt() {
            return Integer.parseInt(next());
        }

        long nextLong() {
            return Long.parseLong(next());
        }
    }

    // Shuffle array before sorting to avoid worst-case quicksort traps
    static final Random random = new Random();
    static void shuffleSort(long[] a) {
        int n = a.length;
        for (int i = 0; i < n; ++i) {
            int j = i + random.nextInt(n - i);
            long temp = a[i];
            a[i] = a[j];
            a[j] = temp;
        }
        Arrays.sort(a);
    }

    public static void main(String[] args) {
        FastScanner fs = new FastScanner();
        PrintWriter out = new PrintWriter(System.out);

        String tStr = fs.next();
        if (tStr != null) {
            int t = Integer.parseInt(tStr);
            while (t-- > 0) {
                int n = fs.nextInt();
                long[] a = new long[n];
                for (int i = 0; i < n; i++) {
                    a[i] = fs.nextLong();
                }

                // Sort array in O(n log n)
                shuffleSort(a);

                int m = n / 4;
                long[] b = new long[n];

                // Quarter mapping:
                // Q1: a[0 ... m-1]
                // Q2: a[m ... 2m-1]
                // Q3: a[2m ... 3m-1]
                // Q4: a[3m ... 4m-1]
                for (int i = 0; i < m; i++) {
                    b[4 * i + 0] = a[3 * m + i]; // Q4 -> (+, +)
                    b[4 * i + 1] = a[m + i];     // Q2 -> (-, +)
                    b[4 * i + 2] = a[2 * m + i]; // Q3 -> (+, -)
                    b[4 * i + 3] = a[i];         // Q1 -> (-, -)
                }

                // Output result
                for (int i = 0; i < n; i++) {
                    out.print(b[i]);
                    if (i + 1 < n) {
                        out.print(" ");
                    } else {
                        out.println();
                    }
                }
            }
        }

        out.flush();
    }
}