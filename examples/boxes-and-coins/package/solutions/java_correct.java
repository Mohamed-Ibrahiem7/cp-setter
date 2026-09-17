import java.io.*;
import java.util.*;

public class java_correct {
    static double solveOne(int n) {
        int size = 2 * (n + 2) + 1;
        int offset = n + 2;

        double[] F_next = new double[size];
        double[] G_next = new double[size];

        for (int i = n; i >= 1; i--) {
            double[] F_cur = new double[size];
            double[] G_cur = new double[size];

            for (int d = -(i + 1); d <= i + 1; d++) {
                int idx = d + offset;
                double score_p1 = (d + 1 > 0) ? 1.0 : 0.0;
                double score_m1 = (d - 1 > 0) ? 1.0 : 0.0;

                int dp1 = d + 1 + offset;
                int dm1 = d - 1 + offset;
                double f_p1 = (dp1 >= 0 && dp1 < size) ? F_next[dp1] : 0.0;
                double f_m1 = (dm1 >= 0 && dm1 < size) ? F_next[dm1] : 0.0;
                double g_p1 = (dp1 >= 0 && dp1 < size) ? G_next[dp1] : 0.0;
                double g_m1 = (dm1 >= 0 && dm1 < size) ? G_next[dm1] : 0.0;

                F_cur[idx] = 0.5 * (score_p1 + f_p1) + 0.5 * (score_m1 + f_m1);

                int d_plus = d + 1;
                int b_plus = (i - d_plus) / 2;
                int d_plus_star = (i + d_plus) / 2 - (b_plus / 2);
                int id_star_p = d_plus_star + offset;
                boolean star_p_ok = (id_star_p >= 0 && id_star_p < size);

                double val_none_p = score_p1 + g_p1;
                double val_halve_p = -1e18;
                if (star_p_ok) {
                    val_halve_p = (d_plus_star > 0 ? 1.0 : 0.0) + F_next[id_star_p];
                }
                double best_p = Math.max(val_none_p, val_halve_p);

                int d_minus = d - 1;
                int b_minus = (i - d_minus) / 2;
                int d_minus_star = (i + d_minus) / 2 - (b_minus / 2);
                int id_star_m = d_minus_star + offset;
                boolean star_m_ok = (id_star_m >= 0 && id_star_m < size);

                double val_none_m = score_m1 + g_m1;
                double val_halve_m = -1e18;
                if (star_m_ok) {
                    val_halve_m = (d_minus_star > 0 ? 1.0 : 0.0) + F_next[id_star_m];
                }
                double best_m = Math.max(val_none_m, val_halve_m);

                G_cur[idx] = 0.5 * best_p + 0.5 * best_m;
            }

            F_next = F_cur;
            G_next = G_cur;
        }

        return G_next[0 + offset];
    }

    public static void main(String[] args) throws IOException {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        PrintWriter out = new PrintWriter(System.out);

        int t = Integer.parseInt(br.readLine());
        while (t-- > 0) {
            int n = Integer.parseInt(br.readLine());
            double ans = solveOne(n);
            out.printf("%.10f%n", ans);
        }
        out.flush();
    }
}
