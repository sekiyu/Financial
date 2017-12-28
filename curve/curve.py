# -*- coding: utf-8 -*-
import numpy as np
import scipy.optimize as so
import interpolation

class Curve(object):
    def __init__(self, 
                 grid_terms,
                 discount_factors,
                 interpolation_method = None):
        self._grid_terms = grid_terms
        self._discount_factors = discount_factors
        self._interpolation_method = interpolation_method 
    
    def get_df(self, t):
        switcher = {
            'log_linear' : interpolation.log_linear,
            'log_cubic' : interpolation.log_cubic,
            'monotone_convex' : interpolation.monotone_convex
            }
        return switcher[self._interpolation_method](t,
                                                    self._grid_terms,
                                                    self._discount_factors)
    
    def _update(self, discount_factors):
        self._discount_factors = discount_factors
        return self
            

def build_curve(curve, instruments, market_rates):
    def loss(dfs):        
        par_rates = np.array(
            [ins.par_rate(curve._update(dfs)) for ins in instruments]).flatten()
        return np.sum(np.power((par_rates - market_rates), 2))
    opt = so.minimize(loss,
                      curve._discount_factors,
                      method = 'Nelder-Mead',
                      tol = 1e-6)
    curve._update(opt.x)
    return curve

def _test_build_curve():
    import instruments as inst    
    import matplotlib.pyplot as plt

    # market data to fit
    start_dates = [0, 0, 0, 0, 0]
    end_dates = [1, 2, 3, 4, 5]
    roll = 0.5
    swap_rates = [0.01, 0.011, 0.012, 0.015, 0.016]
    instruments = [inst.SingleCurrencySwap(start, end, roll) 
        for start, end in zip(start_dates, end_dates)]
            
    # generate curve grids same as swap end dates
    grids = np.array(end_dates)
    dfs = np.exp(-np.array(swap_rates) * grids)
    linear = Curve(grids, dfs, interpolation_method = 'log_linear')
    cubic = Curve(grids, dfs, interpolation_method = 'log_cubic')
    mc = Curve(grids, dfs, interpolation_method = 'monotone_convex')

    built_linear = build_curve(linear, instruments, swap_rates)
    built_cubic = build_curve(cubic, instruments, swap_rates)
    built_mc = build_curve(mc, instruments, swap_rates)

    print('log linear :', [inst.par_rate(built_linear) for inst in instruments])    
    print('log cubic :', [inst.par_rate(built_cubic) for inst in instruments])
    print('monotone convex :', [inst.par_rate(built_mc) for inst in instruments])

    ts = np.arange(0, 5, 1. / 365)

    df_linear = built_linear.get_df(ts)
    df_cubic = built_cubic.get_df(ts)
    df_mc = built_mc.get_df(ts)
    plt.plot(ts, df_linear, label = 'log linear')
    plt.plot(ts, df_cubic, label = 'log cubic')
    plt.plot(ts, df_mc, label = 'monotone convex')
    plt.legend()    
    plt.show()
    
    fwd_linear = -np.log(df_linear[1:] / df_linear[:-1]) / (ts[1:] - ts[:-1])
    fwd_cubic = -np.log(df_cubic[1:] / df_cubic[:-1]) / (ts[1:] - ts[:-1])
    fwd_mc = -np.log(df_mc[1:] / df_mc[:-1]) / (ts[1:] - ts[:-1])
    plt.plot(ts[:-1], fwd_linear, label = 'log linear')
    plt.plot(ts[:-1], fwd_cubic, label = 'log cubic')
    plt.plot(ts[:-1], fwd_mc, label = 'monotone convex')
    plt.legend(bbox_to_anchor=(1.05, 0.5, 0.5, .100))
    plt.show()

def _vectorized_calib():
    import instruments as inst    
    start_dates = np.array([0, 0, 0, 0, 0])
    end_dates = np.array([1, 2, 3, 4, 5])
    swap_rates = np.array([0.01, 0.011, 0.013, 0.015, 0.016])
    insts = inst.SimpleRate(start_dates, end_dates)

    grids = np.array(end_dates)
    dfs = np.exp(-np.array(swap_rates) * grids)
    mc = Curve(grids, dfs, interpolation_method = 'monotone_convex')
    loss = lambda x: np.sum(np.power(insts.par_rate(mc._update(x)) - swap_rates, 2))
    print('before :', loss(dfs))
    param = so.minimize(loss, 
                        dfs,
                        tol = 1e-8)
    print('after:', loss(param.x))

    mc._update(param.x)
    print(insts.par_rate(mc))
    print(param)
    
if __name__ == '__main__':
    _test_build_curve()
#    _vectorized_calib()