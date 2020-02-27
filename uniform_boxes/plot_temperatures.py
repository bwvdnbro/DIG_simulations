import numpy as np
import h5py
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as pl
import scipy.stats as stats
import matplotlib.ticker as ticker

pl.rcParams["text.usetex"] = True
pc = 3.086e16

Zs = [0.0001, 0.004, 0.02, 0.1]
ages = [1.0e6, 1.0e7, 1.0e8, 1.0e9, 1.0e10]
OHs = [-4.0, -3.31, -3.0]


def get_temperature(Z, age, OH):
    fname = "ub_Z{0}_a{1:.0f}_m{2:.2f}_020.hdf5".format(Z, np.log10(age), -OH)
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


pl.rcParams["figure.figsize"] = (9, 6)

fig, ax = pl.subplots(4, 5, sharex=True, sharey=True)

colors = ["C0", "C1", "C2"]
for iZ in range(len(Zs)):
    Z = Zs[iZ]
    for iage in range(len(ages)):
        age = ages[iage]
        for iOH in range(len(OHs)):
            OH = OHs[iOH]
            r, T = get_temperature(Z, age, OH)
            ax[iZ][iage].plot(
                r, T, "-", color=colors[iOH], label="${0}$".format(OH)
            )
            ax[iZ][iage].xaxis.set_minor_locator(ticker.AutoMinorLocator())
            ax[iZ][iage].yaxis.set_minor_locator(ticker.AutoMinorLocator())
            ax[iZ][iage].grid()

ax[1][2].legend(loc="best")

for i in range(4):
    ax[i][0].set_ylabel("$T_e$ (K)")
for i in range(5):
    ax[3][i].set_xlabel("$r$ (pc)")

for iage in range(len(ages)):
    ax[0][iage].set_title(
        "$\\log t_\\star = {0:.1f}$".format(np.log10(ages[iage]))
    )
for iZ in range(len(Zs)):
    pl.text(
        1.02,
        0.5,
        "$\\log Z_\\star={0:.1f}$".format(np.log10(Zs[iZ])),
        horizontalalignment="left",
        verticalalignment="center",
        clip_on=False,
        transform=ax[iZ][4].transAxes,
    )

ax[0][0].set_xlim(0., 4.)
ax[0][0].set_xticks([1., 2., 3.])
fig.subplots_adjust(wspace=0, hspace=0)
pl.savefig("temperatures.png", dpi=300, bbox_inches="tight")
