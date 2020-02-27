import write_parameterfile
import numpy as np

params = write_parameterfile.read_parameterfile("template.param")

Zs = [0.0001, 0.004, 0.02, 0.1]
ages = [1.0e6, 1.0e7, 1.0e8, 1.0e9, 1.0e10]
metallicities = [-4.0, -3.31, -3.0]
for Z in Zs:
    for age in ages:
        for met in metallicities:
            fname = "ub_Z{0}_a{1:.0f}_m{2:.2f}".format(Z, np.log10(age), -met)
            params["PhotonSourceSpectrum:metallicity"] = "{0}".format(Z)
            params["PhotonSourceSpectrum:age in yr"] = "{0}".format(age)
            params["AbundanceModel:metallicity"] = "{0}".format(met)
            params["DensityGridWriter:prefix"] = fname + "_"
            write_parameterfile.write_parameterfile(fname + ".param", params)
