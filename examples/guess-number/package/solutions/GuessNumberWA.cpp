#include <bits/stdc++.h>
using namespace std;
int main() {
     
     int l=1,r=1e9;
     int ans=-1;
     while(l<=r){
         int md=(l+r)/2;
         cout<<md<<endl;
         char x;
         cin>>x;
         if(x=='='){
             cout<<"! "<<50 + 1<<endl;
             return 0;
         }
         else if(x=='>'){
              l = md + 1;
         }
         else r = md- 1;
     }
     cout<<"! 1"<<endl;
    return 0;
}
