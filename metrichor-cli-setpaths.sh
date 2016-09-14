#!/usr/bin/env bash


# Set versions
nvm_version="5.12.0"
metrichor_version="2.40.16"
gcc_version="5.4.0"

# Set and export compiler flags
export CXX=$HOME/.local/easybuild/software/GCC/$gcc_version/bin/g++
export CC=$HOME/.local/easybuild/software/GCC/$gcc_version/bin/gcc
export LD_LIBRARY_PATH=$HOME/.local/easybuild/software/GCC/$gcc_version/lib/:$HOME/.local/easybuild/software/GCC/$gcc_version/lib64/:$LD_LIBRARY_PATH

# Set hdf5 flag
HDF5_HOME=$HOME/src/hdf5/

# Load nvm
export NVM_DIR=$HOME/.nvm
source $NVM_DIR/nvm.sh  # This loads nvm

# source API_KEY
source $HOME/.met_apikey

# export path to metrichor commandline agent
export PATH=$PATH:$HOME/metrichor-cli-2.40.16/bin/

# export node path to link to hdf5 module
export NODE_PATH=$HOME/.nvm/versions/node/v${nvm_version}/lib/node_modules/:$NODE_PATH



