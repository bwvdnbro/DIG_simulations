import write_parameterfile
import numpy as np

params = write_parameterfile.read_parameterfile("template.param")

Qtot = 27 * 1.0e48
for HOLMESfrac in [0.0, 0.003, 0.03, 0.3, 1.0]:
    QOB = (1.0 - HOLMESfrac) * Qtot
    QHOLMES = HOLMESfrac * Qtot
    fname = "R01_RHD_DIG_HOLMESfrac{0}".format(HOLMESfrac)
    if QHOLMES > 0.0:
        params["ContinuousPhotonSource:type"] = "ExtendedDisc"
        params["ContinuousPhotonSource:luminosity"] = "{0} s^-1".format(QHOLMES)
    else:
        params["ContinuousPhotonSource:type"] = "None"
    if QOB > 0.0:
        params["PhotonSourceDistribution:type"] = "DiscPatch"
        params[
            "PhotonSourceDistribution:source luminosity"
        ] = "{0} s^-1".format(QOB / 27.0)
    else:
        params["PhotonSourceDistribution:type"] = "None"
    if QHOLMES > 0.0 and QOB > 0.0:
        params["TaskBasedIonizationSimulation:number of photons"] = "2e8"
    else:
        params["TaskBasedIonizationSimulation:number of photons"] = "1e8"
    params["DensityGridWriter:prefix"] = fname + "_"
    write_parameterfile.write_parameterfile(fname + ".param", params)
