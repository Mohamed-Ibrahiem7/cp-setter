#include <bits/stdc++.h>
#include "testlib.h"
using namespace std;
const int LIMIT_QUERIES = 30;
bool check(string x){
    for(auto i:x){
                if(!isdigit(i)){
                  return 0;
                }
            }
            return 1;
}
int main(int argc, char* argv[]) {
    registerInteraction(argc, argv);
     //inf.init("guess.in",_input);
        int queries = -1;
        int n = inf.readInt(1, 1000000000, "N");
        while (true) {
            if (++queries > LIMIT_QUERIES) {
                string st=to_string(queries);
                st+=" ";
                st += string(to_string(-1));
                tout<<st<<endl;
                break;
            }
            string x = ouf.readToken();
            
            if(!check(x)){
                string st=to_string(queries);
                st+=" ";

                st += string(to_string(-1));
                tout<<st<<endl;
                break;
            }
            
            long long xx=stoll(x);
            if (xx == n) {
                cout << '=' << endl;
                 string y = ouf.readToken();
                 string x = ouf.readToken();
                 if(!check(x)){
                      string st=to_string(queries);
                      st+=" ";
                      st += string(to_string(-1));
                      tout<<st<<endl;
                       break;
                 }
                string st=to_string(queries);
                st+=" ";
                st += x;
                tout<<st<<endl;
                break;
                 
            }
            if(n > xx){
                cout<<">"<<endl;
                
            }
            else{
                cout<<"<"<<endl;
            }
        }
          
    quitf(_ok, "checked");

}
