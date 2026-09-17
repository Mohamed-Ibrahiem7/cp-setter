import java.io.*;
import java.util.Arrays;
public class Main {
    private static double[] fA, fB, gA, gB;
private static double solveOne(int n) {
    int size = 2 * (n + 2) + 1;
    int offset = n + 2;

    Arrays.fill(fA, 0, size, 0.0);
    Arrays.fill(gA, 0, size, 0.0);

    double[] fNext = fA;
    double[] gNext = gA;
    double[] fCur = fB;
    double[] gCur = gB;

    for (int i = n; i >= 1; --i) {
        for (int d = -(i + 1); d <= i + 1; ++d) {
            int idx = d + offset;
            double scoreP1 = d + 1 > 0 ? 1.0 : 0.0;
            double scoreM1 = d - 1 > 0 ? 1.0 : 0.0;

            int dp1 = d + 1 + offset;
            int dm1 = d - 1 + offset;

            double fP1 = dp1 >= 0 && dp1 < size ? fNext[dp1] : 0.0;
            double fM1 = dm1 >= 0 && dm1 < size ? fNext[dm1] : 0.0;
            double gP1 = dp1 >= 0 && dp1 < size ? gNext[dp1] : 0.0;
            double gM1 = dm1 >= 0 && dm1 < size ? gNext[dm1] : 0.0;

            fCur[idx] = 0.5 * (scoreP1 + fP1)
                      + 0.5 * (scoreM1 + fM1);

            int dPlus = d + 1;
            int bPlus = (i - dPlus) / 2;
            int dPlusStar = (i + dPlus) / 2 - bPlus / 2;
            int idStarP = dPlusStar + offset;

            double valNoneP = scoreP1 + gP1;
            double valHalveP = -1e18;
            if (idStarP >= 0 && idStarP < size) {
                valHalveP = (dPlusStar > 0 ? 1.0 : 0.0)
                          + fNext[idStarP];
            }
            double bestP = Math.max(valNoneP, valHalveP);

            int dMinus = d - 1;
            int bMinus = (i - dMinus) / 2;
            int dMinusStar = (i + dMinus) / 2 - bMinus / 2;
            int idStarM = dMinusStar + offset;

            double valNoneM = scoreM1 + gM1;
            double valHalveM = -1e18;
            if (idStarM >= 0 && idStarM < size) {
                valHalveM = (dMinusStar > 0 ? 1.0 : 0.0)
                          + fNext[idStarM];
            }
            double bestM = Math.max(valNoneM, valHalveM);

            gCur[idx] = 0.5 * bestP + 0.5 * bestM;
        }

        double[] temp = fNext;
        fNext = fCur;
        fCur = temp;

        temp = gNext;
        gNext = gCur;
        gCur = temp;
    }

    return gNext[offset];
}

public static void main(String[] args) throws Exception {
    FastInput in = new FastInput(System.in);
    FastOutput out = new FastOutput(System.out);

    int t = in.nextInt();
    int[] values = new int[t];
    int maxN = 0;

    for (int i = 0; i < t; ++i) {
        int n = in.nextInt();
        values[i] = n;
        if (n > maxN) {
            maxN = n;
        }
    }

    int maxSize = 2 * (maxN + 2) + 1;
    fA = new double[maxSize];
    fB = new double[maxSize];
    gA = new double[maxSize];
    gB = new double[maxSize];

    for (int i = 0; i < t; ++i) {
        out.writeFixed10(solveOne(values[i]));
    }

    out.flush();
}

private static final class FastInput {
    private final InputStream input;
    private final byte[] buffer = new byte[1 << 16];
    private int position;
    private int limit;

    FastInput(InputStream input) {
        this.input = input;
    }

    private int read() throws IOException {
        if (position >= limit) {
            limit = input.read(buffer);
            position = 0;
            if (limit <= 0) {
                return -1;
            }
        }
        return buffer[position++];
    }

    int nextInt() throws IOException {
        int c;
        do {
            c = read();
        } while (c <= 32);

        int sign = 1;
        if (c == '-') {
            sign = -1;
            c = read();
        }

        int value = 0;
        while (c > 32) {
            value = value * 10 + c - '0';
            c = read();
        }
        return value * sign;
    }
}

private static final class FastOutput {
    private final OutputStream output;
    private final byte[] buffer = new byte[1 << 16];
    private int position;

    FastOutput(OutputStream output) {
        this.output = output;
    }

    private void writeByte(int value) throws IOException {
        if (position == buffer.length) {
            flushBuffer();
        }
        buffer[position++] = (byte) value;
    }

    private void writeLong(long value) throws IOException {
        if (value == 0) {
            writeByte('0');
            return;
        }

        int start = position;
        while (value > 0) {
            writeByte((int) ('0' + value % 10));
            value /= 10;
        }

        int left = start;
        int right = position - 1;
        while (left < right) {
            byte temp = buffer[left];
            buffer[left++] = buffer[right];
            buffer[right--] = temp;
        }
    }

    void writeFixed10(double value) throws IOException {
        long scaled = Math.round(value * 10000000000.0);
        long integerPart = scaled / 10000000000L;
        long fractionalPart = scaled % 10000000000L;

        writeLong(integerPart);
        writeByte('.');

        long divisor = 1000000000L;
        while (divisor > 0) {
            writeByte((int) ('0' + fractionalPart / divisor));
            fractionalPart %= divisor;
            divisor /= 10;
        }
        writeByte('\n');
    }

    private void flushBuffer() throws IOException {
        output.write(buffer, 0, position);
        position = 0;
    }

    void flush() throws IOException {
        flushBuffer();
        output.flush();
    }
}
}