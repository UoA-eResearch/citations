"""Reviewer check: is 18:00-21:00 NZDT a window when panels produce nothing in Dec-Feb? Solar elevation and a
clear-sky plane-of-array proxy (north-facing, 25 deg tilt) relative to the 12:00-15:00 window."""
import numpy as np
sites = {"Auckland": (-36.85, 174.76), "Christchurch": (-43.53, 172.64), "Invercargill": (-46.41, 168.35)}
def decl(doy): return np.radians(23.45) * np.sin(2*np.pi*(284+doy)/365)
def eot(doy):
    b = 2*np.pi*(doy-81)/364; return 9.87*np.sin(2*b) - 7.53*np.cos(b) - 1.5*np.sin(b)   # minutes
def poa(lat, lon, doy, clock_nzdt, tilt=25.0):
    # NZDT = UTC+13 -> solar time = clock - 13h + lon/15 h + eot
    st = clock_nzdt - 13 + lon/15 + eot(doy)/60
    ha = np.radians(15*(st-12)); la = np.radians(lat); de = decl(doy)
    sinel = np.sin(la)*np.sin(de) + np.cos(la)*np.cos(de)*np.cos(ha)
    el = np.arcsin(np.clip(sinel, -1, 1))
    if el <= 0: return 0.0, np.degrees(el)
    # incidence on a north-facing (azimuth 0 = north in the southern hemisphere) tilted plane
    cosz = sinel; sinz = np.cos(el)
    az = np.arctan2(np.sin(ha), np.cos(ha)*np.sin(la) - np.tan(de)*np.cos(la))   # from north, east positive (approx)
    t = np.radians(tilt)
    cosinc = cosz*np.cos(t) + sinz*np.sin(t)*np.cos(az)
    am = 1/max(sinel, 0.05); dni = 950*0.7**(am**0.678)          # simple clear-sky direct normal (W/m2)
    diff = 0.1*dni
    return max(cosinc, 0)*dni + diff*(1+np.cos(t))/2, np.degrees(el)
for name, (lat, lon) in sites.items():
    for lab, doy in (("Dec 21", 355), ("Jan 20", 20), ("Feb 20", 51)):
        mid = np.mean([poa(lat, lon, doy, h)[0] for h in np.arange(12, 15, 0.25)])
        eve = np.mean([poa(lat, lon, doy, h)[0] for h in np.arange(18, 21, 0.25)])
        el18, el19, el20 = (poa(lat, lon, doy, h)[1] for h in (18, 19, 20))
        print(f"{name:12s} {lab}: sun elevation at 18:00/19:00/20:00 NZDT = {el18:4.0f}/{el19:4.0f}/{el20:4.0f} deg; clear-sky POA evening/midday = {eve/mid:.2f}")
