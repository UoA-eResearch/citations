"""2 m wet-bulb temperature from temperature, dewpoint and surface pressure (plan.md sec 4): the psychrometric equation
e = es(Tw) - gamma(Tw) * p * (T - Tw), gamma = 6.60e-4 * (1 + 0.00115 Tw) per K (Tw in degC, p in hPa), with Bolton (1980)
saturation vapour pressure es(T) = 6.112 exp(17.67 T / (T + 243.5)) hPa; solved by Newton iteration to 1e-4 K."""
import numpy as np


def es(tc):
    return 6.112 * np.exp(17.67 * tc / (tc + 243.5))


def wetbulb(t_k, td_k, p_pa, tol=1e-4, maxit=50):
    t, td, p = np.asarray(t_k, float) - 273.15, np.asarray(td_k, float) - 273.15, np.asarray(p_pa, float) / 100
    td = np.minimum(td, t)
    e = es(td)
    tw = td + (t - td) / 3.0
    for _ in range(maxit):
        g = 6.60e-4 * (1 + 0.00115 * tw)
        f = es(tw) - g * p * (t - tw) - e
        dfd = es(tw) * 17.67 * 243.5 / (tw + 243.5) ** 2 + g * p - 6.60e-4 * 0.00115 * p * (t - tw)
        step = f / dfd
        tw = tw - step
        if np.nanmax(np.abs(step)) < tol:
            break
    return tw + 273.15


def dewpoint_from_rh(t_k, rh):
    """Dewpoint (K) for temperature t_k (K) and relative humidity rh (0-1), inverting Bolton's formula."""
    a = np.log(np.clip(rh, 1e-6, 1) * es(np.asarray(t_k) - 273.15) / 6.112)
    return 243.5 * a / (17.67 - a) + 273.15


def qsat(t_k, p_pa):
    """Saturation specific humidity (kg/kg) over water."""
    e = es(np.asarray(t_k) - 273.15) * 100
    return 0.622 * e / (np.asarray(p_pa) - 0.378 * e)
