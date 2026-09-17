#include <bits/stdc++.h>
using namespace std;

int N;

double dfs(int i, int a, int b, bool can_use) {
    if (i > N) return 0.0;

    double branch_a;
    {
        double score_a = (a + 1 > b) ? 1.0 : 0.0;
        double cont_a = dfs(i + 1, a + 1, b, can_use);
        if (can_use) {
            int b_halve = b / 2;
            double score_a_halve = (a + 1 > b_halve) ? 1.0 : 0.0;
            double cont_a_halve = dfs(i + 1, a + 1, b_halve, false);
            branch_a = max(score_a + cont_a, score_a_halve + cont_a_halve);
        } else {
            branch_a = score_a + cont_a;
        }
    }

    double branch_b;
    {
        double score_b = (a > b + 1) ? 1.0 : 0.0;
        double cont_b = dfs(i + 1, a, b + 1, can_use);
        if (can_use) {
            int b_halve = (b + 1) / 2;
            double score_b_halve = (a > b_halve) ? 1.0 : 0.0;
            double cont_b_halve = dfs(i + 1, a, b_halve, false);
            branch_b = max(score_b + cont_b, score_b_halve + cont_b_halve);
        } else {
            branch_b = score_b + cont_b;
        }
    }

    return 0.5 * branch_a + 0.5 * branch_b;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cout << fixed << setprecision(10);

    int t;
    cin >> t;
    while (t--) {
        cin >> N;
        cout << dfs(1, 0, 0, true) << '\n';
    }
    return 0;
}
