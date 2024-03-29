"""Standard Deviation Filtered, N-Pole Gaussian Filter Indicator by [Loxx]."""

import math
# @version=5
def indicator("STD-Filtered, N-Pole Gaussian Filter [Loxx]",
     shorttitle="STDFNPGF [Loxx]",
     overlay = true)

greencolor = #2DD204
redcolor = #D2042D

# factorial calc
def fact(int n):
    float a = 1
    for i = 1 to n
        a *= i
    a

# alpha calc
def alpha(int period, int poles):
    w = 2.0 * math.pi / period
    float b = (1.0 - math.cos(w)) / (math.pow(1.414, 2.0 / poles) - 1.0)
    float a = - b + math.sqrt(b * b + 2.0 * b)
    return a

# n-pole calc
def makeCoeffs(simple int period, simple int order):
    coeffs = matrix.new<float>(order + 1, 3, 0.)
    float a = _alpha(period, order)
    for r = 0 to order
        out = nz(fact(order) / (fact(order - r) * fact(r)), 1)
        matrix.set(coeffs, r, 0, out)
        matrix.set(coeffs, r, 1, math.pow(a, r))
        matrix.set(coeffs, r, 2, math.pow(1.0 - a, r))
    return coeffs

# n-pole calc
def npolegf(float src, simple int period, simple int order):
    var coeffs = _makeCoeffs(period, order)
    float filt = src * matrix.get(coeffs, order, 1)
    int sign = 1
    for r = 1 to order
        filt += sign * matrix.get(coeffs, r, 0) * matrix.get(coeffs, r, 2) * nz(filt[r])
        sign *= -1
    return filt

# std filter
def filt(float src, int len, float filter):
    float price = src
    float filtdev = filter * ta.stdev(src, len)
    price = math.abs(price - nz(price[1])) < filtdev if nz(price[1]) else price
    return price

smthtype = input.string("Kaufman", "Heiken-Ashi Better Smoothing", options = ["AMA", "T3", "Kaufman"], group=  "Source Settings")
srcoption = input.string("Close", "Source", group= "Source Settings",
     options =
     ["Close", "Open", "High", "Low", "Median", "Typical", "Weighted", "Average", "Average Median Body", "Trend Biased", "Trend Biased (Extreme)",
     "HA Close", "HA Open", "HA High", "HA Low", "HA Median", "HA Typical", "HA Weighted", "HA Average", "HA Average Median Body", "HA Trend Biased", "HA Trend Biased (Extreme)",
     "HAB Close", "HAB Open", "HAB High", "HAB Low", "HAB Median", "HAB Typical", "HAB Weighted", "HAB Average", "HAB Average Median Body", "HAB Trend Biased", "HAB Trend Biased (Extreme)"])

period = input.int(25,'Period', group = "Basic Settings")
order = input.int(5,'Order', group = "Basic Settings", minval = 1)

filterop = input.string("Gaussian Filter", "Filter Options", options = ["Price", "Gaussian Filter", "Both", "None"], group=  "Filter Settings")
filter = input.float(1, "Filter Devaitions", minval = 0, group= "Filter Settings")
filterperiod = input.int(10, "Filter Period", minval = 0, group= "Filter Settings")

colorbars = input.bool(true, "Color bars?", group = "UI Options")
showSigs = input.bool(true, "Show signals?", group= "UI Options")

kfl=input.float(0.666, title="* Kaufman's Adaptive MA (KAMA) Only - Fast End", group = "Moving Average Inputs")
ksl=input.float(0.0645, title="* Kaufman's Adaptive MA (KAMA) Only - Slow End", group = "Moving Average Inputs")
amafl = input.int(2, title="* Adaptive Moving Average (AMA) Only - Fast", group = "Moving Average Inputs")
amasl = input.int(30, title="* Adaptive Moving Average (AMA) Only - Slow", group = "Moving Average Inputs")

[haclose, haopen, hahigh, halow, hamedian, hatypical, haweighted, haaverage] = request.security(ticker.heikinashi(syminfo.tickerid), timeframe.period, [close, open, high, low, hl2, hlc3, hlcc4, ohlc4])

float src = switch srcoption
	"Close" : loxxexpandedsourcetypes.rclose()
	"Open" : loxxexpandedsourcetypes.ropen()
	"High" : loxxexpandedsourcetypes.rhigh()
	"Low" : loxxexpandedsourcetypes.rlow()
	"Median" : loxxexpandedsourcetypes.rmedian()
	"Typical" : loxxexpandedsourcetypes.rtypical()
	"Weighted" : loxxexpandedsourcetypes.rweighted()
	"Average" : loxxexpandedsourcetypes.raverage()
    "Average Median Body" : loxxexpandedsourcetypes.ravemedbody()
	"Trend Biased" : loxxexpandedsourcetypes.rtrendb()
	"Trend Biased (Extreme)" : loxxexpandedsourcetypes.rtrendbext()
	"HA Close" : loxxexpandedsourcetypes.haclose(haclose)
	"HA Open" : loxxexpandedsourcetypes.haopen(haopen)
	"HA High" : loxxexpandedsourcetypes.hahigh(hahigh)
	"HA Low" : loxxexpandedsourcetypes.halow(halow)
	"HA Median" : loxxexpandedsourcetypes.hamedian(hamedian)
	"HA Typical" : loxxexpandedsourcetypes.hatypical(hatypical)
	"HA Weighted" : loxxexpandedsourcetypes.haweighted(haweighted)
	"HA Average" : loxxexpandedsourcetypes.haaverage(haaverage)
    "HA Average Median Body" : loxxexpandedsourcetypes.haavemedbody(haclose, haopen)
	"HA Trend Biased" : loxxexpandedsourcetypes.hatrendb(haclose, haopen, hahigh, halow)
	"HA Trend Biased (Extreme)" : loxxexpandedsourcetypes.hatrendbext(haclose, haopen, hahigh, halow)
	"HAB Close" : loxxexpandedsourcetypes.habclose(smthtype, amafl, amasl, kfl, ksl)
	"HAB Open" : loxxexpandedsourcetypes.habopen(smthtype, amafl, amasl, kfl, ksl)
	"HAB High" : loxxexpandedsourcetypes.habhigh(smthtype, amafl, amasl, kfl, ksl)
	"HAB Low" : loxxexpandedsourcetypes.hablow(smthtype, amafl, amasl, kfl, ksl)
	"HAB Median" : loxxexpandedsourcetypes.habmedian(smthtype, amafl, amasl, kfl, ksl)
	"HAB Typical" : loxxexpandedsourcetypes.habtypical(smthtype, amafl, amasl, kfl, ksl)
	"HAB Weighted" : loxxexpandedsourcetypes.habweighted(smthtype, amafl, amasl, kfl, ksl)
	"HAB Average" : loxxexpandedsourcetypes.habaverage(smthtype, amafl, amasl, kfl, ksl)
    "HAB Average Median Body" : loxxexpandedsourcetypes.habavemedbody(smthtype, amafl, amasl, kfl, ksl)
	"HAB Trend Biased" : loxxexpandedsourcetypes.habtrendb(smthtype, amafl, amasl, kfl, ksl)
	"HAB Trend Biased (Extreme)" : loxxexpandedsourcetypes.habtrendbext(smthtype, amafl, amasl, kfl, ksl)
	: haclose

src := filterop == "Both" or filterop == "Price" and filter > 0 ? _filt(src, filterperiod, filter) : src

out = _npolegf(src, period, order)

out := filterop == "Both" or filterop == "Gaussian Filter" and filter > 0 ? _filt(out, filterperiod, filter) : out

sig = nz(out[1])

state = 0
if (out > sig)
    state := 1
if (out < sig)
    state := -1

pregoLong = out > sig and (nz(out[1]) < nz(sig[1]) or nz(out[1]) == nz(sig[1]))
pregoShort = out < sig and (nz(out[1]) > nz(sig[1]) or nz(out[1]) == nz(sig[1]))

contsw = 0
contsw := nz(contsw[1])
contsw := pregoLong ? 1 : pregoShort ? -1 : nz(contsw[1])

goLong = pregoLong and nz(contsw[1]) == -1
goShort = pregoShort and nz(contsw[1]) == 1

var color colorout = na
colorout := state == -1 ? redcolor : state == 1 ? greencolor : nz(colorout[1])

plot(out, "N-Pole GF", color = colorout, linewidth = 3)
barcolor(colorbars ? colorout : na)

plotshape(showSigs and goLong, title = "Long", color = color.yellow, textcolor = color.yellow, text = "L", style = shape.triangleup, location = location.belowbar, size = size.tiny)
plotshape(showSigs and goShort, title = "Short", color = color.fuchsia, textcolor = color.fuchsia, text = "S", style = shape.triangledown, location = location.abovebar, size = size.tiny)

alertcondition(goLong, title = "Long", message = "STD-Filtered, N-Pole Gaussian Filter [Loxx]: Long\nSymbol: {{ticker}}\nPrice: {{close}}")
alertcondition(goShort, title = "Short", message = "STD-Filtered, N-Pole Gaussian Filter [Loxx]: Short\nSymbol: {{ticker}}\nPrice: {{close}}")
