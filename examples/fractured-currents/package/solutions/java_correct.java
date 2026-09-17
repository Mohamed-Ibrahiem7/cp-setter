import java.io.*;
import java.util.*;

public class java_correct {
    static final int BITS = 30;
    static final long MOD = 1_000_000_007L;

    static int n;
    static long[] value;

    static int[] head;
    static int[] to;
    static int[] next;
    static int[] edgeId;
    static int edgeCount;

    static int[] tin;
    static int[] low;
    static int[] parent;
    static int[] parentEdge;
    static int[] iterator;
    static int[] subtreeSize;
    static int[] stack;

    static int[][] bitCount;

    static int timer;

    static void addArc(int u, int v, int id) {
        to[edgeCount] = v;
        edgeId[edgeCount] = id;
        next[edgeCount] = head[u];
        head[u] = edgeCount++;
    }

    static void initializeVertex(int u) {
        tin[u] = low[u] = ++timer;
        subtreeSize[u] = 1;
        iterator[u] = head[u];

        long x = value[u];

        for (int bit = 0; bit < BITS; ++bit) {
            bitCount[u][bit] =
                (int) ((x >>> bit) & 1L);
        }
    }

    public static void main(String[] args) throws Exception {
        FastScanner in = new FastScanner(System.in);

        n = in.nextInt();
        int m = in.nextInt();

        value = new long[n + 1];

        for (int i = 1; i <= n; ++i) {
            value[i] = in.nextLong();
        }

        head = new int[n + 1];
        Arrays.fill(head, -1);

        to = new int[2 * m];
        next = new int[2 * m];
        edgeId = new int[2 * m];

        for (int id = 0; id < m; ++id) {
            int u = in.nextInt();
            int v = in.nextInt();

            addArc(u, v, id);

            if (u != v) {
                addArc(v, u, id);
            }
        }

        tin = new int[n + 1];
        Arrays.fill(tin, -1);

        low = new int[n + 1];
        parent = new int[n + 1];

        parentEdge = new int[n + 1];
        Arrays.fill(parentEdge, -1);

        iterator = new int[n + 1];
        subtreeSize = new int[n + 1];
        bitCount = new int[n + 1][BITS];
        stack = new int[n];

        long totalScore = 0;
        long maximumLoss = 0;

        int[] bridgeChildren = new int[n];

        for (int root = 1; root <= n; ++root) {
            if (tin[root] != -1) {
                continue;
            }

            int bridgeCount = 0;
            int top = 0;

            parent[root] = 0;
            initializeVertex(root);
            stack[top++] = root;

            while (top > 0) {
                int u = stack[top - 1];
                int arc = iterator[u];

                if (arc != -1) {
                    iterator[u] = next[arc];

                    if (edgeId[arc] == parentEdge[u]) {
                        continue;
                    }

                    int v = to[arc];

                    if (tin[v] == -1) {
                        parent[v] = u;
                        parentEdge[v] = edgeId[arc];

                        initializeVertex(v);
                        stack[top++] = v;
                    } else {
                        low[u] = Math.min(
                            low[u],
                            tin[v]
                        );
                    }
                } else {
                    --top;

                    int p = parent[u];

                    if (p != 0) {
                        low[p] = Math.min(
                            low[p],
                            low[u]
                        );

                        subtreeSize[p] += subtreeSize[u];

                        for (int bit = 0; bit < BITS; ++bit) {
                            bitCount[p][bit] +=
                                bitCount[u][bit];
                        }

                        if (low[u] > tin[p]) {
                            bridgeChildren[bridgeCount++] = u;
                        }
                    }
                }
            }

            long componentSize = subtreeSize[root];

            for (int bit = 0; bit < BITS; ++bit) {
                long ones = bitCount[root][bit];
                long zeros = componentSize - ones;

                totalScore +=
                    ones * zeros * (1L << bit);
            }

            for (int index = 0;
                 index < bridgeCount;
                 ++index) {

                int child = bridgeChildren[index];

                long childSize = subtreeSize[child];
                long otherSize =
                    componentSize - childSize;

                long loss = 0;

                for (int bit = 0; bit < BITS; ++bit) {
                    long childOnes =
                        bitCount[child][bit];

                    long childZeros =
                        childSize - childOnes;

                    long otherOnes =
                        bitCount[root][bit] - childOnes;

                    long otherZeros =
                        otherSize - otherOnes;

                    loss += (
                        childOnes * otherZeros
                        + childZeros * otherOnes
                    ) * (1L << bit);
                }

                maximumLoss =
                    Math.max(maximumLoss, loss);
            }
        }

        long answer = (
            (totalScore % MOD)
            - (maximumLoss % MOD)
            + MOD
        ) % MOD;

        System.out.println(answer);
    }

    static final class FastScanner {
        private final InputStream in;
        private final byte[] buffer =
            new byte[1 << 16];

        private int pointer = 0;
        private int length = 0;

        FastScanner(InputStream in) {
            this.in = in;
        }

        private int read() throws IOException {
            if (pointer >= length) {
                length = in.read(buffer);
                pointer = 0;

                if (length <= 0) {
                    return -1;
                }
            }

            return buffer[pointer++];
        }

        long nextLong() throws IOException {
            int c;

            do {
                c = read();
            } while (c <= 32 && c != -1);

            long sign = 1;

            if (c == '-') {
                sign = -1;
                c = read();
            }

            long result = 0;

            while (c > 32 && c != -1) {
                result =
                    result * 10 + (c - '0');
                c = read();
            }

            return result * sign;
        }

        int nextInt() throws IOException {
            return (int) nextLong();
        }
    }
}