# -*- coding: utf-8 -*-
import numpy as np
from typing import Callable
import curve_wrapper as cw

class HoLee(object):
    def __init__(self, 
                 volatility: float, 
                 curve_initial, 
                 t_initial: float = 0):
        self.__volatility = volatility
        self.__curve = curve_initial
        self.__t_initial = t_initial
        
    def get_curve(self, 
                  t_observe: float, 
                  r_observe: float):
        return cw.CurveWrppaer(
            lambda t_maturity : self.func_a(t_observe, t_maturity) 
                * np.exp(-self.func_b(t_observe, t_maturity) * r_observe))

    def func_a(self, 
               t_observe: float, 
               t_maturity: float) -> float:
        initial = (self.__curve.get_df(t_maturity - self.__t_initial) 
            / self.__curve.get_df(t_observe - self.__t_initial))
        evolve = np.exp(-self.func_b(t_observe, t_maturity) * self.dlnPdT(t_observe)
            - 1 / 2 * self.__volatility**2 * (t_observe - self.__t_initial) * self.func_b(t_observe, t_maturity)**2)
        return initial * evolve

    def func_b(self, 
               t_obesrve: float, 
               t_maturity: float) -> float:
        return t_maturity - t_obesrve
    
    def dlnPdT(self, 
               t_observe: float) -> float:
        shock = 1/365
        p = np.log(self.__curve.get_df(t_observe - self.__t_initial + shock))        
        n = np.log(self.__curve.get_df(t_observe - self.__t_initial - shock))
        return (p - n) / (2 * shock)

if __name__ == '__main__':
    print('test')
