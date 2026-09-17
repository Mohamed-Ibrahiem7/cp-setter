#include <bits/stdc++.h>
using namespace std;
int main() {
     
     int l=1,r=1e7;
     while(l<=r){
         int md=l;
         cout<<md<<endl;
         char x;
         cin>>x;
         if(x=='='){
             cout<<"! "<<md<<endl;
             break;
         }
         l++;
     }
    return 0;
}
