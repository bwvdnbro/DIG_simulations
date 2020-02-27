import numpy as np
import h5py
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as pl
import scipy.stats as stats
import matplotlib.ticker as ticker

pl.rcParams["text.usetex"] = True
pc = 3.086e16

Ts = [5000.0, 12000.0, 20000.0, 40000.0, 100000.0]
OHs = [-4.0, -3.31, -3.0]


def get_temperature(T, OH):
    fname = "bb_T{0:.0f}_m{1:.2f}_020.hdf5".format(T, -OH)
    file = h5py.File(fname, "r")
    box = file["/Header"].attrs["BoxSize"]
    coords = file["/PartType0/Coordinates"][:]
    coords[:, 0] -= 0.5 * box[0]
    coords[:, 1] -= 0.5 * box[1]
    coords[:, 2] -= 0.5 * box[2]
    r = np.sqrt(coords[:, 0] ** 2 + coords[:, 1] ** 2 + coords[:, 2] ** 2) / pc
    temp = file["/PartType0/Temperature"][:]

    Tbin, rbin, _ = stats.binned_statistic(r, temp, statistic="mean", bins=100)

    rbin = 0.5 * (rbin[1:] + rbin[:-1])
    return rbin, Tbin


pl.rcParams["figure.figsize"] = (9, 2)

fig, ax = pl.subplots(1, 5, sharex=True, sharey=True)

colors = ["C0", "C1", "C2"]
for iT in range(len(Ts)):
    for iOH in range(len(OHs)):
        OH = OHs[iOH]
        r, T = get_temperature(Ts[iT], OH)
        ax[iT].plot(r, T, "-", color=colors[iOH], label="${0}$".format(OH))
        ax[iT].xaxis.set_minor_locator(ticker.AutoMinorLocator())
        ax[iT].yaxis.set_minor_locator(ticker.AutoMinorLocator())
        ax[iT].grid()

ax[0].legend(loc="best")

ax[0].set_ylabel("$T_e$ (K)")
for i in range(5):
    ax[i].set_xlabel("$r$ (pc)")

for iT in range(len(Ts)):
    ax[iT].set_title("$T = {0:.0f}$ K".format(Ts[iT]))

ax[0].set_xlim(0.0, 4.0)
ax[0].set_xticks([1.0, 2.0, 3.0])
fig.subplots_adjust(wspace=0, hspace=0)
pl.savefig("bb_temperatures.png", dpi=300, bbox_inches="tight")
