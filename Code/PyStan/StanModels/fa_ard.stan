data{
    int<lower=0> N;// number  of  datapoints
    int<lower=0> D;// number  of  dimensions  in  observed  dataset
    int<lower=0> M;// number  of  dimensions  in  latent  dataset
    vector[D] x[N];//  observations
}


parameters{
    matrix[M,N] z;  // latent data
    matrix[D,M] W;  // factor loadings
    vector<lower=0>[D] sigma;   //  standard  deviations
    vector[D] mu;   //  added means
    vector<lower=0>[M] alpha;  // variance explained by observed variables
    //vector<lower=0>[M] beta;   // variance explained by latent variables
}

transformed parameters{
    vector[M] mean_z;
    matrix[M,M] cov_z;
    
    for (m in 1:M){
        mean_z[m] = 0.0;
        for (n in 1:M){
            if (m==n){
                cov_z[m,n]=1.0;
            } else{
                cov_z[m,n]=0.0;
            }
        }
    }
}

model{
    //  priors
    //for (m in 1:M){
        //W[:,m] ~ normal(0.0,alpha);
        //}
        
    for (d in 1:D){
        W[d] ~ normal(0.0,alpha);
    //    mu[d]~normal(0.0, 5.0) ;
        }
        
    //sigma~lognormal(0.0, 1.0) ;
    alpha~inv_gamma(1.0,1.0);
    //beta~inv_gamma(1.0,1.0);
    
    
    //  likelihood
    for (n in 1:N){
        z[:,n] ~ multi_normal(mean_z, cov_z);
        x[n] ~ normal(W*col(z,n)+mu, sigma);
        }
        
}