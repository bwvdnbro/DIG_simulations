import numpy as np
import h5py
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as pl
import argparse
import os

pl.rcParams["text.usetex"] = True

lines = [
    "Halpha",
    "Hbeta",
    "OI_6300",
    "OII_3727",
    "OIII_5007",
    "SII_6725",
    "NII_6584",
    "HeI_5876",
]

# parse command line arguments
argparser = argparse.ArgumentParser(
    "Plot an image using data from the given image file."
)
argparser.add_argument(
    "--file",
    "-f",
    help="Image file containing the image data.",
    action="store",
    required=True,
)
argparser.add_argument(
    "--output",
    "-o",
    help="Name of the output image file (PNG).",
    action="store",
    required=True,
)
argparser.add_argument(
    "--resolution",
    "-r",
    help="Resolution of the image.",
    action="store",
    choices=["high", "low", "nodust"],
    required=True,
)
argparser.add_argument(
    "--quantity",
    "-q",
    help="Quantity to output.",
    action="store",
    choices=lines,
    required=True,
)
args = argparser.parse_args()

# check that the input file exists
if not os.path.exists(args.file):
    print('Input file "{0}" not found!'.format(args.file))

# select the right image group for the requested resolution
if args.resolution == "high":
    group = "/hires/"
elif args.resolution == "nodust":
    group = "/hires_nodust/"
else:
    group = "/lowres/"

# some unit constants used below
kpc = 3.086e19  # m
Lsol = 3.828e26  # J s^-1

# open the file
file = h5py.File(args.file, "r")
# read the pixels and convert to kpc
px = file[group + "PixelCoordinatesX"][:] / kpc
py = file[group + "PixelCoordinatesY"][:] / kpc
# read the requested image
image = file[group + args.quantity][:]

# plot the image
cs = pl.pcolormesh(px, py, image / Lsol, norm=matplotlib.colors.LogNorm())
pl.gca().set_aspect("equal")

# add a colorbar
pl.colorbar(cs, label=args.quantity + " ($L_\\odot{}$)")

# add axis labels
pl.xlabel("$x$ (kpc)")
pl.ylabel("$z$ (kpc)")

# save the image
pl.tight_layout()
pl.savefig(args.output, dpi=300, bbox_inches="tight")
