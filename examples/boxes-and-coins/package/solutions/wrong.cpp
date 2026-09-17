#include <bits/stdc++.h>
using namespace std;

double solveOne(int n) {
    int size = 2 * (n + 2) + 1;
    int offset = n + 2;

    vector<double> F_next(size, 0.0);
    vector<double> G_next(size, 0.0);

    for (int i = n; i >= 1; i--) {
        vector<double> F_cur(size, 0.0);
        vector<double> G_cur(size, 0.0);

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
            bool star_p_ok = (id_star_p >= 0 && id_star_p < size);

            double score_star_p = (d_plus_star > 0) ? 1.0 : 0.0;
            double best_p;
            if (score_p1 == 0.0 && score_star_p == 1.0 && star_p_ok) {
                best_p = score_star_p + F_next[id_star_p];
            } else {
                best_p = score_p1 + g_p1;
            }

            int d_minus = d - 1;
            int b_minus = (i - d_minus) / 2;
            int d_minus_star = (i + d_minus) / 2 - (b_minus / 2);
            int id_star_m = d_minus_star + offset;
            bool star_m_ok = (id_star_m >= 0 && id_star_m < size);

            double score_star_m = (d_minus_star > 0) ? 1.0 : 0.0;
            double best_m;
            if (score_m1 == 0.0 && score_star_m == 1.0 && star_m_ok) {
                best_m = score_star_m + F_next[id_star_m];
            } else {
                best_m = score_m1 + g_m1;
            }

            G_cur[idx] = 0.5 * best_p + 0.5 * best_m;
        }

        F_next.swap(F_cur);
        G_next.swap(G_cur);
    }

    return G_next[0 + offset];
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cout << fixed << setprecision(10);

    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        cout << solveOne(n) << '\n';
    }
    return 0;
}
