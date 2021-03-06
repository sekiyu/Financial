# -*- coding: utf-8 -*-
import numpy as np
from scipy import integrate
from scipy import real
import black_scholes as bs
import scipy.optimize as so

def heston_call(fwd, strike, tau, v0, vbar, kappa, xi, rho):
    '''
    Calculate Call Option Price Under Heston Model
    '''
    x = np.log(fwd / strike)
    P0 = _P(0, x, tau, v0, vbar, kappa, xi, rho)
    P1 = _P(1, x, tau, v0, vbar, kappa, xi, rho)
    return fwd * P1 - strike * P0

def heston_put(fwd, strike, tau, v0, vbar, kappa, xi, rho):
    '''
    Calculate Put Option Price Under Heston Model
    '''
    return fwd - strike - heston_call(fwd, strike, tau, v0, vbar, kappa, xi, rho)

def _CD(i, w, tau, kappa, xi, rho):
    a = -w**2 / 2. - 1j * w /2. + i * 1j * w
    b = kappa - rho * xi * (i + w * 1j)
    c = xi**2 / 2.

    alphaplus = (b + np.sqrt(b**2 - 4. * a * c)) / (2. * c)
    alphaminus = (b - np.sqrt(b**2 - 4. * a * c)) / (2. * c)
    eroot = np.exp(-np.sqrt(b**2 - 4. * a * c) * tau)
    C = kappa * (alphaminus * tau
                 - 2. / xi**2 * np.log((1 - alphaminus / alphaplus * eroot)
                                        / (1 - alphaminus / alphaplus)))
    D = alphaminus * (1 - eroot) / (1 - alphaminus / alphaplus * eroot)
    return C,D

def _integrand(i, x, w, tau, v0, vbar, kappa, xi, rho):
    C, D = _CD(i, w, tau, kappa, xi, rho)
    return real(np.exp(C * vbar + D * v0 + 1j * w * x) / (1j * w))

def _P(i, x, tau, v0, vbar, kappa, xi, rho):
    integrand = lambda w: _integrand(i, x, w, tau, v0, vbar, kappa, xi, rho)
    return 1. / 2. + 1. / np.pi * integrate.quad(integrand, 0, np.inf)[0]

def implied_volatility(fwd, strike, tau, v0, vbar, kappa, xi, rho):
    return bs.implied_black_volatility(
        heston_call(fwd, strike, tau, v0, vbar, kappa, xi, rho),
        fwd,
        strike,
        tau)

def strike_by_delta(fwd, delta, tau, v0, vbar, kappa, xi, rho):
    '''
    Calculate Corresponding Strike Under Heston Model
    '''
    error = lambda strike : bs.black_delta(
        fwd, strike, implied_volatility(fwd, strike, tau, v0, vbar, kappa, xi, rho), tau) - delta - (1 if delta < 0 else 0)
    return so.newton(error, x0 = fwd)


def _test_speed():
    import matplotlib.pyplot as plt
    import time
    f = 100
    strike = 110
    tau = 1
    v = 0.02
    vbar = 0.02
    kappa = 1
    xi = 1
    rho = -0.2
    price = heston_call(f, strike, tau, v, vbar, kappa, xi, rho)
    print('Heston :', price)
    price_bs = bs.black_call(f, strike, np.sqrt(v), tau)
    print('BS :', price_bs)

    strikes = np.arange(0.5 * f, 1.5 * f, step = f / 100.)
    prices = [heston_call(f, k, tau, v, vbar, kappa, xi, rho) for k in strikes]
    t0 = time.time()
    volatilities = bs.implied_black_volatilities(np.array(prices), f, np.array(strikes), tau)
    t1 = time.time()
    volatilities = [bs.implied_black_volatility(v, f, k, tau) for v, k in zip(prices, strikes)]
    t2 = time.time()
    print('Multidimensional roots finding :', t1 - t0)
    print('Scalar roots finding :', t2 - t1)
    plt.plot(strikes, volatilities)


if __name__ == '__main__':
    fwd = 100
    strike = 110
    tau = 1
    vbar = 0.02
    v0 = vbar
    kappa = 1
    xi = 1
    rho = -0.2

    vol = implied_volatility(fwd, strike, tau, v0, vbar, kappa, xi, rho)
    print(vol)
    delta = 0.25
    k = strike_by_delta(fwd, delta, tau, v0, vbar, kappa, xi, rho)
    print(k)
