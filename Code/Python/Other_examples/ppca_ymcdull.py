import numpy as np
from scipy import special
from numpy.random import randn
from numpy.matlib import repmat

## updating W, X and tau when doing inference
class PPCA:
    ## Y: input continuous data with shape (N, M)
    ## D: number of ppca components
    def __init__(self, D = 2, n_iters = 100, verbose = False):
        self.D = D
        self.n_iters = n_iters
        self.verbose = verbose
        
    def _init_paras(self, N, M, D):
        self.a = 1.0
        self.b = 1.0
        self.e_tau = self.a / self.b
        self.e_w = randn(M, D)
        self.e_wwt = np.zeros((D, D, M))
        for m in range(M):
            ## use np.newaxis here to transfer numpy array from 1D to 2D
            self.e_wwt[:, :, m] = np.eye(D) + self.e_w[m, :][np.newaxis].T.dot(self.e_w[m, :][np.newaxis])

        self.tol = 1e-3
        self.lbs = []
        self.e_X = np.zeros((N, D))
        self.e_XXt = np.zeros((D, D, N))

    def _update_X(self, Y, N, D):
        self.sigx = np.linalg.inv(np.eye(D) + self.e_tau * np.sum(self.e_wwt, axis = 2))
        for n in range(N):
            self.e_X[n, :] = self.e_tau * self.sigx.dot(np.sum(self.e_w * np.tile(Y[n, :], (D, 1)).T, axis = 0))
            self.e_XXt[:, :, n] = self.sigx + self.e_X[n, :][np.newaxis].T.dot(self.e_X[n, :][np.newaxis])

    def _update_W(self, Y, M, D):
        self.sigw = np.linalg.inv(np.eye(D) + self.e_tau * np.sum(self.e_XXt, axis = 2))
        for m in range(M):
            self.e_w[m, :] = self.e_tau * self.sigw.dot(np.sum(self.e_X * np.tile(Y[:, m], (D, 1)).T, axis = 0))
            self.e_wwt[:, :, m] = self.sigw + self.e_w[m, :][np.newaxis].T.dot(self.e_w[m, :][np.newaxis])

    def _update_tau(self, Y, M, N):
        self.e = self.a + N * M * 1.0 / 2
        outer_expect = 0
        for n in range(N):
            for m in range(M):
                outer_expect = outer_expect \
                                + np.trace(self.e_wwt[:, :, m].dot(self.sigx)) \
                                + self.e_X[n, :][np.newaxis].dot(self.e_wwt[:, :, m]).dot(self.e_X[n, :][np.newaxis].T)[0][0]
        self.f = self.b + 0.5 * np.sum(Y ** 2) - np.sum(Y * self.e_w.dot(self.e_X.T).T) + 0.5 * outer_expect
        self.e_tau = self.e / self.f
        self.e_log_tau = np.mean(np.log(np.random.gamma(self.e, 1/self.f, size=1000)))
    
    def lower_bound(self,Y, M, N, D):
        LB = self.a * np.log(self.b) + (self.a - 1) * self.e_log_tau - self.b * self.e_tau - special.gammaln(self.a)
        LB = LB - (self.e * np.log(self.f) + (self.e - 1) * self.e_log_tau - self.f * self.e_tau - special.gammaln(self.e))
        for n in range(N):
            LB = LB + (-(D*0.5)*np.log(2*np.pi) - 0.5 * (np.trace(self.sigx) + self.e_X[n, :][np.newaxis].dot(self.e_X[n, :][np.newaxis].T)[0][0]))
            LB = LB - (-(D*0.5)*np.log(2*np.pi) - 0.5 * np.log(np.linalg.det(self.sigx)) - 0.5 * D)
        for m in range(M):
            LB = LB + (-(D*0.5)*np.log(2*np.pi) - 0.5 * (np.trace(self.sigw) + self.e_w[m, :][np.newaxis].dot(self.e_w[m, :][np.newaxis].T)[0][0]))
            LB = LB - (-(D*0.5)*np.log(2*np.pi) - 0.5 * np.log(np.linalg.det(self.sigw)) - 0.5 * D)
        outer_expect = 0
        for n in range(N):
            for m in range(M):
                outer_expect = outer_expect \
                                + np.trace(self.e_wwt[:, :, m].dot(self.sigx)) \
                                + self.e_X[n, :][np.newaxis].dot(self.e_wwt[:, :, m]).dot(self.e_X[n, :][np.newaxis].T)[0][0]

        LB = LB + ( \
            -(N * M * 1.0 / 2) * np.log(2 * np.pi) + (N * M * 1.0 / 2) * self.e_log_tau \
            - 0.5 * self.e_tau * (np.sum(Y**2) - 2 * np.sum(Y * self.e_w.dot(self.e_X.T).T) + outer_expect))
        return LB
    
    def _update(self, Y, N, M, D):
        self._update_X(Y, N, D)
        self._update_W(Y, M, D)
        self._update_tau(Y, M, N)
        LB = self.lower_bound(Y, M, N, D)
        self.lbs.append(LB)
        if self.verbose:
            print("Lower bound: {}".format(LB))
       
    def fit(self, Y):
        N, M = Y.shape
        D = self.D
#         temporarily comment these two lines out
#         if not D:
#             D = N
        self._init_paras(N, M, D)

        for it in range(self.n_iters):
            self._update(Y, N, M, D)
            if self.verbose:
                print(it)
            if it >= 1:
                if np.abs(self.lbs[it] - self.lbs[it - 1]) < self.tol:
                    break

    def recover(self):
        return self.e_X.dot(self.e_w.T)