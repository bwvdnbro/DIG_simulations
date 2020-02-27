#! /bin/bash

if [ "$#" -ne 3 ]; then
  echo "Usage: ./runscript.sh PATH_TO_CMACIONIZE_EXECUTABLE" \
       " NUMBER_OF_PARALLEL_SIMULATIONS NUMBER_OF_THREADS_PER_SIMULATION"
  exit
fi

cmacionize=$1
numparallel=$2
numthread=$3

# create the parameter files (add the parent directory to the PYTHONPATH
#  because that is where write_parameterfile.py is located)
PYTHONPATH=../ python3 create_parameter_files.py

# run the simulations, in parallel
ls ub*.param | parallel -j $numparallel \
  $cmacionize --params {} --threads $numthread --task-based --no-initial-output

# create the temperature plot
python3 plot_temperatures.py
