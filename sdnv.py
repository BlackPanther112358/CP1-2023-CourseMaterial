#include<bits/stdc++.h>
using namespace std;
typedef long long ll;
typedef unsigned long long ull;
typedef long double ld;
#define fastInp cin.tie(0); cout.tie(0); ios_base::sync_with_stdio(0);
template<class T> void printVec(vector<T> &vec){for(ll i=0;i<vec.size();i++){cout<<vec[i]<<','<<' ';}cout<<endl;}
vector<ll> toReach(1000,1e9);
void preComp(){
    toReach[0] = 0;
    toReach[1] = 0;
    toReach[2] = 1;
    for(int i=3;i<1000;i++){
        for(int j = 1;j<i;j++){
            if((i-j)%j == 0){
                // cout<<"i: "<<i<<", j: "<<j<<"toReach["<<i-j<<"] is "<<toReach[i-j]<<endl;
                toReach[i] = min(toReach[i],toReach[i-j]+1);
            }
        }
    }
}
int main(){
fastInp;
    preComp();
    // printVec(toReach);

     ll t;
     cin>>t;
        while(t--){
            ll n,k;
            cin>>n>>k;
            vector<ll> w(n),v(n);
            ll x;
            for(ll i=0;i<n;i++){
            cin>>x;
            w[i] = toReach[x];
            }
            for(ll i=0;i<n;i++)cin>>v[i];
            vector<ll> dp(k+1,0);
            for(int i=0;i<n;i++){
                for(int j = k;j>=0;j--){
                    if(j+w[i]<k+1){
                        dp[j+w[i]] = max(dp[j+w[i]],dp[j] + v[i]);
                    }
                }
                // printVec(dp)s
            }
            ll ans = 0;
            for(auto &it: dp)ans = max(ans,it);
            cout<<ans<<endl;
        }

 return 0;
}