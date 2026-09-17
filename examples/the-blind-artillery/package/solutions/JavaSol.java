import java.util.Scanner;

public class JavaSol {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        if (!sc.hasNextInt()) return;
        int tc = sc.nextInt();
        
        while (tc-- > 0) {
            int t1 = -1, t2 = -1;
            
            int l = 1, r = 1000000000;
            while (l <= r) {
                int m = l + (r - l) / 2;
                System.out.println("? " + m);
                System.out.flush();
                
                int p = sc.nextInt();
                int d = sc.nextInt();
                
                if (p == -2 && d == -2) System.exit(0);
                
                if (p == 0 && d == 1) {
                    t1 = m;
                    break;
                }
                
                if (p == -1 && d == 1) {
                    l = m + 1;
                } else {
                    r = m - 1;
                }
            }
            
            l = 1;
            r = 1000000000;
            while (l <= r) {
                int m = l + (r - l) / 2;
                System.out.println("? " + m);
                System.out.flush();
                
                int p = sc.nextInt();
                int d = sc.nextInt();
                
                if (p == -2 && d == -2) System.exit(0);
                
                if (p == 0 && d == -1) {
                    t2 = m;
                    break;
                }
                
                if (p == -1 && d == -1) {
                    r = m - 1;
                } else {
                    l = m + 1;
                }
            }
            
            System.out.println("! " + t1 + " " + t2);
            System.out.flush();
        }
        sc.close();
    }
}