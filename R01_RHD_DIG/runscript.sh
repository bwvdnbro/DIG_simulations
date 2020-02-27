#! /bin/bash

if [ "$#" -ne 3 ]; then
  echo "Usage: ./runscript.sh PATH_TO_CMACIONIZE_EXECUTABLE" \
       " NUMBER_OF_PARALLEL_SIMULATIONS NUMBER_OF_THREADS_PER_SIMULATION"
  exit
fi

cmacionize=$1
numparallel=$2
numthread=$3

# download the initial condition file
./get_IC_file.sh

# create the parameter files (add the parent directory to the PYTHONPATH
#  because that is where write_parameterfile.py is located)
PYTHONPATH=../ python3 create_parameter_files.py

# run the simulations, in parallel
ls R01*.param | parallel -j $numparallel \
  $cmacionize --params {} --threads $numthread --task-based --no-initial-output

# run the line emission simulations, in parallel
ls R01*_020.hdf5 | parallel -j $numparallel \
  $cmacionize --params emission.param --file {} --emission --threads $numthread

# create image cubes for all the simulations, in parallel
ls R01*_020.hdf5 | parallel -j $numparallel \
  python3 make_image_cube.py --file {} --output {.}_image.hdf5
