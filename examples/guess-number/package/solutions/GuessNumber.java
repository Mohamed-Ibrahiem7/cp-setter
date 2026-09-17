/* package whatever; // don't place package name! */

import java.util.*;
import java.lang.*;
import java.io.*;

/* Name of the class has to be "Main" only if the class is public. */
public class GuessNumber
{
	public static void main (String[] args) throws java.lang.Exception
	{
		Scanner sc = new Scanner(System.in);
		PrintWriter out = new PrintWriter(System.out);

    	int l=1;
    	int r= (int) 1e9;
		 while(l<=r){
		     int md=(l+r)/2;
		     out.println(md);
		     out.flush();
		     char x = sc.next().charAt(0);
		     if(x=='='){
		     	out.println("! " + md);
		     	out.flush();
		         break;
		     }
		     else if(x=='>'){
		          l = md + 1;
		     }
		     else r = md- 1;
		 }
		 out.close();
	}
	
	static class Scanner
	{
		StringTokenizer st;
		BufferedReader br;
 
		public Scanner(InputStream s){	br = new BufferedReader(new InputStreamReader(s));}
 
		public Scanner(FileReader s) throws FileNotFoundException {	br = new BufferedReader(s);}
 
		public String next() throws IOException
		{
			while (st == null || !st.hasMoreTokens())
				st = new StringTokenizer(br.readLine());
			return st.nextToken();
		}
 
		public int nextInt() throws IOException {return Integer.parseInt(next());}
 
		public long nextLong() throws IOException {return Long.parseLong(next());}
 
		public String nextLine() throws IOException {return br.readLine();}
 
		public double nextDouble() throws IOException { return Double.parseDouble(next()); }
 
		public boolean ready() throws IOException {return br.ready();}
	}

}
