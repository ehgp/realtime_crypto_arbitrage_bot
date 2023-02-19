"""Standard Deviation Filtered, N-Pole Gaussian Filter Library by [Loxx]."""

import math

# # @version=5
def library("loxxexpandedsourcetypes", overlay = true)

def ama(src, len, fl, sl):
    flout = 2/(fl + 1)
    slout = 2/(sl + 1)
    hh = ta.highest(len + 1)
    ll = ta.lowest(len + 1)
    mltp = hh - ll != 0 if math.abs(2 * src - ll - hh) / (hh - ll) else 0
    ssc = mltp * (flout - slout) + slout
    ama = 0
    ama := nz(ama[1]) + math.pow(ssc, 2) * (src - nz(ama[1]))
    return ama

def t3(src, len):
    xe1_1 = ta.ema(src, len)
    xe2_1 = ta.ema(xe1_1, len)
    xe3_1 = ta.ema(xe2_1, len)
    xe4_1 = ta.ema(xe3_1, len)
    xe5_1 = ta.ema(xe4_1, len)
    xe6_1 = ta.ema(xe5_1, len)
    b_1 = 0.7
    c1_1 = -b_1 * b_1 * b_1
    c2_1 = 3 * b_1 * b_1 + 3 * b_1 * b_1 * b_1
    c3_1 = -6 * b_1 * b_1 - 3 * b_1 - 3 * b_1 * b_1 * b_1
    c4_1 = 1 + 3 * b_1 + b_1 * b_1 * b_1 + 3 * b_1 * b_1
    nT3Average = c1_1 * xe6_1 + c2_1 * xe5_1 + c3_1 * xe4_1 + c4_1 * xe3_1
    return nT3Average

_kama(src, len, kama_fastend, kama_slowend) =>
    xvnoise = math.abs(src - src[1])
    nfastend = kama_fastend
    nslowend = kama_slowend
    nsignal = math.abs(src - src[len])
    nnoise = math.sum(xvnoise, len)
    nefratio = nnoise != 0 ? nsignal / nnoise : 0
    nsmooth = math.pow(nefratio * (nfastend - nslowend) + nslowend, 2)
    nAMA = 0.0
    nAMA := nz(nAMA[1]) + nsmooth * (src - nz(nAMA[1]))
    nAMA

_trendreg(o, h, l, c)=>
    compute = 0.
    if (c > o)
        compute := ((h + c)/2.0)
    else
        compute := ((l + c)/2.0)
    compute

_trendext(o, h, l, c) =>
    compute = 0.
    if (c > o)
        compute := h
    else if (c < o)
        compute := l
    else
        compute := c
    compute

#  @function rClose: regular close
#  @returns float
export rclose() => close

#  @function rClose: regular open
#  @returns float
export ropen() => open

#  @function rClose: regular high
#  @returns float
export rhigh() => high

#  @function rClose: regular low
#  @returns float
export rlow() => low

#  @function rClose: regular hl2
#  @returns float
export rmedian() =>  hl2

#  @function rClose: regular hlc3
#  @returns float
export rtypical() =>  hlc3

#  @function rClose: regular hlcc4
#  @returns float
export rweighted() =>  hlcc4

#  @function rClose: regular ohlc4
#  @returns float
export raverage() =>  ohlc4

#  @function rClose: median body
#  @returns float
export ravemedbody() => (open + close)/2

#  @function rClose: trend regular
#  @returns float
export rtrendb() => _trendreg(ropen(), rhigh(), rlow(), rclose())

#  @function rClose: trend extreme
#  @returns float
export rtrendbext() => _trendext(ropen(), rhigh(), rlow(), rclose())



# heiken-ashi regular


#  @function haclose: heiken-ashi close
#  @param haclose float
#  @returns float
export haclose(float haclose) => haclose

#  @function haopen: heiken-ashi open
#  @param haopen float
#  @returns float
export haopen(float haopen) => haopen

#  @function hahigh: heiken-ashi high
#  @param hahigh float
#  @returns float
export hahigh(float hahigh) => hahigh

#  @function halow: heiken-ashi low
#  @param halow float
#  @returns float
export halow(float halow) => halow

#  @function hamedian: heiken-ashi median
#  @param hamedian float
#  @returns float
export hamedian(float hamedian) => hamedian

#  @function hatypical: heiken-ashi typical
#  @param hatypical float
#  @returns float
export hatypical(float hatypical) => hatypical

#  @function haweighted: heiken-ashi weighted
#  @param haweighted float
#  @returns float
export haweighted(float haweighted) => haweighted

#  @function haaverage: heiken-ashi average
#  @param haweighted float
#  @returns float
export haaverage(float haweighted) => haweighted

#  @function haavemedbody: heiken-ashi median body
#  @param haclose float
#  @param haopen float
#  @returns float
export haavemedbody(float haclose, float haopen) => (haopen(haopen) + haclose(haclose))/2

#  @function hatrendb: heiken-ashi trend
#  @param haclose float
#  @param haopen float
#  @param hahigh float
#  @param halow float
#  @returns float
export hatrendb(float haclose, float haopen, float hahigh, float halow) => _trendreg(haopen(haopen), hahigh(hahigh), halow(halow), haclose(haclose))

#  @function hatrendext: heiken-ashi trend extreme
#  @param haclose float
#  @param haopen float
#  @param hahigh float
#  @param halow float
#  @returns float
export hatrendbext(float haclose, float haopen, float hahigh, float halow) => _trendext(haopen(haopen), hahigh(hahigh), halow(halow), haclose(haclose))



# heiken-ashi better

_habingest() =>
    out =  (ropen() + rclose())/2 + (((rclose() - ropen())/(rhigh() - rlow())) * math.abs((rclose() - ropen())/2))
    out := na(out) ? rclose() : out
    out
#  @function habclose: heiken-ashi better open
#  @param smthtype string
#  @param amafl int
#  @param amasl int
#  @param kfl int
#  @param ksl int
#  @returns float
export habclose(string smthtype, int amafl, int amasl, float kfl, float ksl) =>
    amaout = _ama(_habingest(), 2, amafl, amasl)
    t3out = _t3(_habingest(), 3)
    kamaout = _kama(_habingest(), 2, kfl, ksl)
    smthtype == "AMA" ? amaout : smthtype == "T3" ? t3out : kamaout

#  @function habopen: heiken-ashi better open
#  @param smthtype string
#  @param amafl int
#  @param amasl int
#  @param kfl int
#  @param ksl int
#  @returns float
export habopen(string smthtype, int amafl, int amasl, float kfl, float ksl) =>
    habopen = 0.
    habopen := na(habopen[1]) ? (nz(habopen) + nz(habclose(smthtype, amafl, amasl, kfl, ksl)[1]))/2 : (nz(habopen[1]) + nz(habclose(smthtype, amafl, amasl, kfl, ksl)[1]))/2
    habopen

#  @function habhigh: heiken-ashi better high
#  @param smthtype string
#  @param amafl int
#  @param amasl int
#  @param kfl int
#  @param ksl int
#  @returns float
export habhigh(string smthtype, int amafl, int amasl, float kfl, float ksl) =>
    math.max(rhigh(), habopen(smthtype, amafl, amasl, kfl, ksl), habclose(smthtype, amafl, amasl, kfl, ksl))

#  @function hablow: heiken-ashi better low
#  @param smthtype string
#  @param amafl int
#  @param amasl int
#  @param kfl int
#  @param ksl int
#  @returns float
export hablow(string smthtype, int amafl, int amasl, float kfl, float ksl) =>
    math.min(rlow(), habopen(smthtype, amafl, amasl, kfl, ksl), habclose(smthtype, amafl, amasl, kfl, ksl))

#  @function habmedian: heiken-ashi better median
#  @param smthtype string
#  @param amafl int
#  @param amasl int
#  @param kfl int
#  @param ksl int
#  @returns float
export habmedian(string smthtype, int amafl, int amasl, float kfl, float ksl) =>
    (habhigh(smthtype, amafl, amasl, kfl, ksl) + hablow(smthtype, amafl, amasl, kfl, ksl))/2

#  @function habtypical: heiken-ashi better typical
#  @param smthtype string
#  @param amafl int
#  @param amasl int
#  @param kfl int
#  @param ksl int
#  @returns float
export habtypical(string smthtype, int amafl, int amasl, float kfl, float ksl) =>
    (habhigh(smthtype, amafl, amasl, kfl, ksl) + hablow(smthtype, amafl, amasl, kfl, ksl) + habclose(smthtype, amafl, amasl, kfl, ksl))/3

#  @function habweighted: heiken-ashi better weighted
#  @param smthtype string
#  @param amafl int
#  @param amasl int
#  @param kfl int
#  @param ksl int
#  @returns float
export habweighted(string smthtype, int amafl, int amasl, float kfl, float ksl) =>
    (habhigh(smthtype, amafl, amasl, kfl, ksl) + hablow(smthtype, amafl, amasl, kfl, ksl) + habclose(smthtype, amafl, amasl, kfl, ksl) + habclose(smthtype, amafl, amasl, kfl, ksl))/4

#  @function habaverage: heiken-ashi better average
#  @param smthtype string
#  @param amafl int
#  @param amasl int
#  @param kfl int
#  @param ksl int
#  @returns float
export habaverage(string smthtype, int amafl, int amasl, float kfl, float ksl) => # ohlc4
    (habopen(smthtype, amafl, amasl, kfl, ksl) + habhigh(smthtype, amafl, amasl, kfl, ksl) + hablow(smthtype, amafl, amasl, kfl, ksl) + habclose(smthtype, amafl, amasl, kfl, ksl))/4

#  @function habavemedbody: heiken-ashi better median body
#  @param smthtype string
#  @param amafl int
#  @param amasl int
#  @param kfl int
#  @param ksl int
#  @returns float
export habavemedbody(string smthtype, int amafl, int amasl, float kfl, float ksl) => # oc2
    (habopen(smthtype, amafl, amasl, kfl, ksl) + habclose(smthtype, amafl, amasl, kfl, ksl))/2

#  @function habtrendb: heiken-ashi better trend
#  @param smthtype string
#  @param amafl int
#  @param amasl int
#  @param kfl int
#  @param ksl int
#  @returns float
export habtrendb(string smthtype, int amafl, int amasl, float kfl, float ksl) =>
    _trendreg(habopen(smthtype, amafl, amasl, kfl, ksl), habhigh(smthtype, amafl, amasl, kfl, ksl), hablow(smthtype, amafl, amasl, kfl, ksl), habclose(smthtype, amafl, amasl, kfl, ksl))

#  @function habtrendbext: heiken-ashi better trend extreme
#  @param smthtype string
#  @param amafl int
#  @param amasl int
#  @param kfl int
#  @param ksl int
#  @returns float
export habtrendbext(string smthtype, int amafl, int amasl, float kfl, float ksl) =>
    _trendext(habopen(smthtype, amafl, amasl, kfl, ksl), habhigh(smthtype, amafl, amasl, kfl, ksl), hablow(smthtype, amafl, amasl, kfl, ksl), habclose(smthtype, amafl, amasl, kfl, ksl))


# example ussage

habcloser = habclose("AMA", 6, 20, 5, 25)
plot(habcloser)
