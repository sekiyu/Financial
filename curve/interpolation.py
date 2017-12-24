# -*- coding: utf-8 -*-
import numpy as np
from scipy import interpolate

def log_linear(t, grids, discount_factors):
    if not(np.isclose(grids[0], 0)):
        grids = np.append([0], grids)
        discount_factors = np.append(1, discount_factors)

    f = interpolate.interp1d(grids, 
                             np.log(discount_factors), 
                             kind = 'linear',
                             fill_value = 'extrapolate')
    return np.exp(f(t))

def log_quadratic(t, grids, discount_factors):
    if not(np.isclose(grids[0], 0)):
        grids = np.append([0], grids)
        discount_factors = np.append(1, discount_factors)
    f = interpolate.interp1d(grids, 
                             np.log(discount_factors), 
                             kind = 'quadratic')
    return np.exp(f(t))

def log_cubic(t, grids, discount_factors):
    if not(np.isclose(grids[0], 0)):
        grids = np.append([0], grids)
        discount_factors = np.append(1, discount_factors)

    f = interpolate.interp1d(grids, 
                             np.log(discount_factors), 
                             kind = 'cubic')
    return np.exp(f(t))


def monotone_convex(t, grids, discount_factors):
    if not(np.isclose(grids[0], 0)):
        grids = np.append([0], grids)
        discount_factors = np.append(1, discount_factors)
        
    f_discrete = -(np.log(discount_factors[1:] / discount_factors[:-1])
                  / (grids[1:] - grids[:-1]))
    f = ((grids[1:-1] -  grids[:-2]) * f_discrete[1:]
        + (grids[2:] -  grids[1:-1]) * f_discrete[:-1]) / (grids[2:] - grids[:-2])
    f0 = (3. * f_discrete[0] - f[0]) / 2.
    fn = (3. * f_discrete[-1] - f[-1]) / 2.
    f = np.append([f0], f)
    f = np.append(f, fn)
    
    indice = np.min(np.where(t.reshape(len(t), 1) < grids.reshape(1, len(grids)), 
                             np.arange(len(grids)), 
                             np.inf),
                    axis = 1)
    indice = np.array(indice, dtype = 'int16')
    f_iminus1 = f[indice - 1]
    f_i = f[indice]
    fd_i = f_discrete[indice - 1]
#    f_iminus1 = interpolate.interp1d(grids, f, kind = 'zero')(t)
#    f_i = interpolate.interp1d(grids[:-1], f[1:], kind = 'zero', fill_value = 'extrapolate')(t)
#    fd_i = interpolate.interp1d(grids[:-1], f_discrete, kind = 'zero', fill_value = 'extrapolate')(t)
    g0 = f_iminus1 - fd_i
    g1 = f_i - fd_i
    dg0 = -4. * g0 - 2. * g1
    dg1 = 2. * g0 + 4. * g1
    t_iminus1 = grids[indice - 1]
    t_i = grids[indice]
#    t_iminus1 = interpolate.interp1d(grids, grids, kind = 'zero')(t)
#    t_i = interpolate.interp1d(grids[:-1], grids[1:], kind = 'zero', fill_value = 'extrapolate')(t)
    x = (t - t_iminus1) / (t_i - t_iminus1)
    def integrate_g(x, g0, g1):
        # region(i)
        Gi = g0 * (x - 2. * x**2  + x**3) + g1 * (-x**2 + x**3)
        # region(ii)
        eta = 1 + 3. * g0 / (g1 - g0)
        Gii = g0 * x + np.where(x < eta, 0, (g1 - g0) * (x - eta)**3 / (1 - eta)**2 / 3.)
        # region(iii)
        eta = 3. * g1 / (g1 - g0)
        Giii = g1 * x + (g0 - g1) / 3. * (eta - np.where(x < eta, (eta - x)**3 / eta**2,  0))
        # region(iv)
        eta = g1 / (g0 + g1)
        A = -g0 * g1 / (g0 + g1)
        Giv = A * x + np.where(x < eta, 
                               1. / 3. * (g0 - A) * (eta - (eta - x)**3 / eta**2), 
                               1. / 3. * (g0 - A) * eta + 1. / 3. * (g1 - A) * (x - eta)**3 / (1 - eta)**2)
        G = [[Gi, Gii], [Giii, Giv]]
        return G
    g = integrate_g(x, g0, g1)
    G = np.where(np.isclose(x, 0), 0, np.where(g0 * g1 < 0,
                 np.where(dg0 * dg1 >= 0, g[0][0], g[0][1]),
                 np.where(dg0 * dg1 >= 0, g[1][0], g[1][1])))
    df = discount_factors[indice - 1]
#    df = interpolate.interp1d(grids, discount_factors, kind = 'zero')(t)
    return df * np.exp(-G - fd_i * (t - t_iminus1))

    

def _slow_log_linear(t, grids, discount_factors):
    if not(np.isclose(grids[0], 0)):
        grids = np.append([0], grids)
        discount_factors = np.append(1, discount_factors)

    f99 = np.log(discount_factors[-2] / discount_factors[-1]) / (grids[-1] - grids[-2])
    df99 = discount_factors[-1] * np.exp(-f99 * (99 - grids[-1]))
    grids = np.append(grids, [99])
    discount_factors = np.append(discount_factors, df99)
    
    
    i = np.where(grids > t)[0][0]
    f = np.log(discount_factors[i - 1] / discount_factors[i]) / (grids[i] - grids[i - 1])
    return discount_factors[i - 1] * np.exp(-f * (t - grids[i - 1]))


def _test_compare_speed():
    import matplotlib.pyplot as plt
    import time

    t = 0.5
    grids = [1,2,3,4]
    dfs = [0.99, 0.98,0.97,0.96]
    print(log_linear(t, grids, dfs))

    ts = np.arange(0, 10, 1./365.)
    
    t0 = time.time()
    df1 = np.array([_slow_log_linear(t, grids, dfs) for t in ts])
    t1 = time.time()
    df2 = log_linear(ts, grids, dfs)
    t2 = time.time()
    plt.plot(ts, df1 - df2, label = 'diff')
    plt.legend()
    plt.show()
    print('slow :', t1 - t0)
    print('broadcast :', t2 - t1)
    
    
    fwd = -np.log(df1[1:] / df1[:-1]) / (ts[1:] - ts[:-1])
#    plt.plot(ts[:-1], fwd)    
        

def _test_curve_shape():
    import matplotlib.pyplot as plt
    grids = [1,2,3,4]
    dfs = [0.993, 0.98,0.975,0.95]

    ts = np.arange(0, 4, 1./365.)
    
    df_linear = log_linear(ts, grids, dfs)
    df_cubic = log_cubic(ts, grids, dfs)
    df_quadratic = log_quadratic(ts, grids, dfs)
    plt.plot(ts, df_linear, label = 'linear')
    plt.plot(ts, df_quadratic, label = 'quadratic')
    plt.plot(ts, df_cubic, label = 'cubic')
    plt.legend()
    plt.show()

    fwd_linear = -np.log(df_linear[1:] / df_linear[:-1]) / (ts[1:] - ts[:-1])
    fwd_quadratic = -np.log(df_quadratic[1:] / df_quadratic[:-1]) / (ts[1:] - ts[:-1])
    fwd_cubic = -np.log(df_cubic[1:] / df_cubic[:-1]) / (ts[1:] - ts[:-1])
    plt.plot(ts[:-1], fwd_linear, label = 'linear')
    plt.plot(ts[:-1], fwd_quadratic, label = 'quadratic')
    plt.plot(ts[:-1], fwd_cubic, label = 'cubic')
    plt.legend()
    plt.show()
    
def _test_monotone_ceonvex():
    import matplotlib.pyplot as plt

    ts = np.arange(0, 5, 1./365.)
    grids = np.array([1,2,3,4,5])
    dfs = np.array([0.99, 0.98, 0.975,0.96, 0.94])

    dfs_mc = monotone_convex(ts, grids, dfs)
    dfs_ll = log_linear(ts, grids, dfs)
    plt.plot(ts, dfs_mc, label = 'monotone_convex')
    plt.plot(ts, dfs_ll, label = 'log_linear')
    plt.legend()
    plt.show()
    fwd = -np.log(dfs_mc[1:] / dfs_mc[:-1]) / (ts[1:] - ts[:-1])
    fwd_ll = -np.log(dfs_ll[1:] / dfs_ll[:-1]) / (ts[1:] - ts[:-1])
    plt.plot(ts[:-1], fwd, label = 'monotone_convex')
    plt.plot(ts[:-1], fwd_ll, label = 'log_linear')
    plt.legend()
    plt.show()
    print(ts)
    print(fwd)
    
if __name__ == '__main__':
#    t = 1.5
#    grids = [1,2,3,4]
#    dfs = [0.993, 0.98,0.975,0.95]
#
#    print(interpolate.interp1d(grids, dfs, kind = 'zero')(t))

#    _test_curve_shape()
    _test_monotone_ceonvex()