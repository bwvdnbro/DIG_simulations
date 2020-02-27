import numpy as np
import h5py
import re
import scipy.stats as stats
import scipy.ndimage as ndimage
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as pl
import argparse

# parse command line arguments
argparser = argparse.ArgumentParser(
    "Create an image data cube from the given CMacIonize snapshot file."
)
argparser.add_argument(
    "--file",
    "-f",
    help="Name of the CMacIonize snapshot file.",
    action="store",
    required=True,
)
argparser.add_argument(
    "--output",
    "-o",
    help="Name of the image data cube output file (created, overwritten if it already exists).",
    action="store",
    required=True,
)
args = argparser.parse_args()

# some global defines
# regular expressions for reading in int and length arrays
intarray = re.compile("\[([0-9]*), ([0-9]*), ([0-9]*)\]")
lengtharray = re.compile(
    "\[([\-0-9\.e\+]*) m, ([\-0-9\.e\+]*) m, ([\-0-9\.e\+]*) m\]"
)

# match between CMacIonize emission line names and their wavelenght
# (in Angstrom)
# used by attenuate() to apply wavelength dependent corrections
wavelengths = {
    "Halpha": 6563.0,
    "Hbeta": 4861.0,
    "OI_6300": 6300.0,
    "OII_3727": 3727.0,
    "OIII_5007": 5007.0,
    "SII_6725": 6725.0,
    "NII_6584": 6584.0,
    "HeI_5876": 5876.0,
}

# create an image from the given cube of emission lines that accounts for
# extinction by dust using a constant dust opacity
# the constant opacity is chosen so that the average optical depth in the
# centre of the box is equal to the given target value
def attenuate(boxsize, density, lines, linenames, target_tau=2.0):

    nz = density.shape[2]
    # compute the average density in the centre
    # we use a 2-pixel layer and average out over all values
    avg_density = density[:, :, nz // 2 : (nz // 2 + 1)].mean()
    # compute the opacity
    opacity = target_tau / (avg_density * boxsize[1])

    # attenuate the lines
    images = []
    taufactors = []
    ds = boxsize[1] / density.shape[1]
    # first compute the wavelength specific correction factors for all lines
    # and the pixel contributions for the first slice of cells
    for iline in range(len(lines)):
        images.append(np.zeros((density.shape[0], density.shape[2])))
        images[-1] += lines[iline][:, 0, :] * ds
        taufactors.append((wavelengths[linenames[iline]] / 5500.0) ** (-0.7))
    # now add the contributions for all other slices of cells
    # note that we do not account for extinction within each cell
    for i in range(1, density.shape[1]):
        for j in range(len(lines)):
            images[j] = (
                images[j]
                * np.exp(-opacity * density[:, i, :] * ds * taufactors[j])
                + lines[j][:, i, :] * ds
            )

    dx = boxsize[0] / density.shape[0]
    dz = boxsize[0] / density.shape[0]
    for i in range(len(lines)):
        images[i] *= dx * dz

    return images


# open the file
file = h5py.File(args.file, "r")

# read grid parameters
res_x, res_y, res_z = intarray.search(
    file["/Parameters"].attrs["DensityGrid:number of cells"].decode("utf-8")
).groups()
res = np.array([int(res_x), int(res_y), int(res_z)], dtype=np.uint32)
ch_x, ch_y, ch_z = intarray.search(
    file["/Parameters"]
    .attrs["DensitySubGridCreator:number of subgrids"]
    .decode("utf-8")
).groups()
chunks = np.array([int(ch_x), int(ch_y), int(ch_z)], dtype=np.uint32)
chunksize = res // chunks

# read box dimensions
ax, ay, az = lengtharray.search(
    file["/Parameters"].attrs["SimulationBox:anchor"].decode("utf-8")
).groups()
sx, sy, sz = lengtharray.search(
    file["/Parameters"].attrs["SimulationBox:sides"].decode("utf-8")
).groups()
box_anchor = np.array([float(ax), float(ay), float(az)], dtype=np.float32)
box_sides = np.array([float(sx), float(sy), float(sz)], dtype=np.float32)

# create the density and emission cubes
denscube = np.zeros((res[0], res[1], res[2]))
linecube = []
linenames = []
for line in wavelengths:
    linecube.append(np.zeros((res[0], res[1], res[2])))
    linenames.append(line)

# now read the chunks and put their data in the density and emission cubes
startchunk = 0
endchunk = chunksize[0] * chunksize[1] * chunksize[2]
chunk_length = chunksize[0] * chunksize[1] * chunksize[2]
max_chunk = res[0] * res[1] * res[2]
chunk_shape = (chunksize[0], chunksize[1], chunksize[2])
ix = 0
iy = 0
iz = 0
while endchunk <= max_chunk:
    line = []
    for linename in wavelengths:
        line.append(file["/PartType0/" + linename][startchunk:endchunk])
    dens = file["/PartType0/NumberDensity"][startchunk:endchunk]

    denscube[
        ix : ix + chunksize[0], iy : iy + chunksize[1], iz : iz + chunksize[2]
    ] = dens.reshape(chunk_shape)
    for iline in range(len(linecube)):
        linecube[iline][
            ix : ix + chunksize[0],
            iy : iy + chunksize[1],
            iz : iz + chunksize[2],
        ] = line[iline].reshape(chunk_shape)

    startchunk += chunk_length
    endchunk += chunk_length

    iz += chunksize[2]
    if iz == res[2]:
        iz = 0
        iy += chunksize[1]
        if iy == res[1]:
            iy = 0
            ix += chunksize[0]

# close the input file, we are done with it
file.close()

# set up the pixel grid
# we store the positions of the corner(s) and the centre of each pixel
ip1xgrid = np.linspace(box_anchor[0], box_anchor[0] + box_sides[0], res[0] + 1)
ixgrid = 0.5 * (ip1xgrid[1:] + ip1xgrid[:-1])
ip1ygrid = np.linspace(box_anchor[2], box_anchor[2] + box_sides[2], res[2] + 1)
iygrid = 0.5 * (ip1ygrid[1:] + ip1ygrid[:-1])

xgrid, ygrid = np.meshgrid(ixgrid, iygrid, indexing="ij")
p1xgrid, p1ygrid = np.meshgrid(ip1xgrid, ip1ygrid, indexing="ij")

# open the output file and dump the high resolution (original) image
# we only dump the corners of the pixels
file = h5py.File(args.output, "w")
linegrid = [
    line.mean(axis=1)
    * box_sides[1]
    * (box_sides[0] / res[0])
    * (box_sides[2] / res[2])
    for line in linecube
]
file.create_group("/hires_nodust")
file.create_dataset(
    "/hires_nodust/PixelCoordinatesX",
    dtype=np.float64,
    data=p1xgrid,
    compression="gzip",
    compression_opts=9,
    shuffle=True,
)
file["/hires_nodust/PixelCoordinatesX"].attrs["Unit"] = np.string_("m")
file.create_dataset(
    "/hires_nodust/PixelCoordinatesY",
    dtype=np.float64,
    data=p1ygrid,
    compression="gzip",
    compression_opts=9,
    shuffle=True,
)
file["/hires_nodust/PixelCoordinatesY"].attrs["Unit"] = np.string_("m")
for iline in range(len(linenames)):
    file.create_dataset(
        "/hires_nodust/" + linenames[iline],
        dtype=np.float64,
        data=linegrid[iline],
        compression="gzip",
        compression_opts=9,
        shuffle=True,
    )
    file["/hires_nodust/" + linenames[iline]].attrs["Unit"] = np.string_(
        "J s^-1"
    )


# get the line emission images by attenuating them appropriately
linegrid = attenuate(box_sides, denscube, linecube, linenames, 10.0)

# now dump the dust attenuated image
file.create_dataset(
    "/hires/PixelCoordinatesX",
    dtype=np.float64,
    data=p1xgrid,
    compression="gzip",
    compression_opts=9,
    shuffle=True,
)
file["/hires/PixelCoordinatesX"].attrs["Unit"] = np.string_("m")
file.create_dataset(
    "/hires/PixelCoordinatesY",
    dtype=np.float64,
    data=p1ygrid,
    compression="gzip",
    compression_opts=9,
    shuffle=True,
)
file["/hires/PixelCoordinatesY"].attrs["Unit"] = np.string_("m")
for iline in range(len(linenames)):
    file.create_dataset(
        "/hires/" + linenames[iline],
        dtype=np.float64,
        data=linegrid[iline],
        compression="gzip",
        compression_opts=9,
        shuffle=True,
    )
    file["/hires/" + linenames[iline]].attrs["Unit"] = np.string_("J s^-1")

# now degrade the image to account for observational effects
for iline in range(len(linegrid)):
    linegrid[iline] = ndimage.gaussian_filter(
        linegrid[iline], sigma=32, mode=["wrap", "nearest"]
    )
    linegrid[iline], _, _, _ = stats.binned_statistic_2d(
        xgrid.flatten(),
        ygrid.flatten(),
        linegrid[iline].flatten(),
        statistic="sum",
        bins=(linegrid[iline].shape[0] // 32, linegrid[iline].shape[1] // 32),
    )
# degrade the pixel positions
# we still use the corners of each pixel
p1xgrid = p1xgrid[::32, ::32]
p1ygrid = p1ygrid[::32, ::32]

# now dump the degraded image as well
file.create_group("/lowres")
file.create_dataset(
    "/lowres/PixelCoordinatesX",
    dtype=np.float64,
    data=p1xgrid,
    compression="gzip",
    compression_opts=9,
    shuffle=True,
)
file["/lowres/PixelCoordinatesX"].attrs["Unit"] = np.string_("m")
file.create_dataset(
    "/lowres/PixelCoordinatesY",
    dtype=np.float64,
    data=p1ygrid,
    compression="gzip",
    compression_opts=9,
    shuffle=True,
)
file["/lowres/PixelCoordinatesY"].attrs["Unit"] = np.string_("m")
for iline in range(len(linenames)):
    file.create_dataset(
        "/lowres/" + linenames[iline],
        dtype=np.float64,
        data=linegrid[iline],
        compression="gzip",
        compression_opts=9,
        shuffle=True,
    )
    file["/lowres/" + linenames[iline]].attrs["Unit"] = np.string_("J s^-1")

file.close()
