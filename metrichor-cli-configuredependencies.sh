#!/usr/bin/env bash

# Prior to running this script you will need to unzip the metrichor tarball into your home directory.
# You will need to have installed a gcc, I've found 5.4.0 works well.
# You can use easybuild to install a gcc compiler without root permissions see here:
# https://github.com/hpcugent/easybuild/wiki/Step-by-step-guide
# To install hdf5 check out this website here:
# http://nugridstars.org/work-packages/io-technologies/hdf5-useepp-format/installing-hdf5

# This script is designed to allow those without root permissions to install metrichor into their home-directory.
current_directory=$(echo $(pwd))

# Set versions
nvm_version="5.12.0"
metrichor_version="2.40.16"
gcc_version="5.4.0"

# Set and export compiler flags
export CXX=$HOME/.local/easybuild/software/GCC/${gcc_version}/bin/g++
export CC=$HOME/.local/easybuild/software/GCC/${gcc_version}/bin/gcc
export LD_LIBRARY_PATH=$HOME/.local/easybuild/software/GCC/${gcc_version}/lib/:$HOME/.local/easybuild/software/GCC/${gcc_version}/lib64/:${LD_LIBRARY_PATH}

# Set hdf5 flag
HDF5_HOME=$HOME/src/hdf5/

# Install nvm
cd $HOME/nvm-master
./install.sh


export NVM_DIR=$HOME/.nvm
source ${NVM_DIR}/nvm.sh  # This loads nvm

#Change to metrichor directory and install nvm and npm
cd $HOME/metrichor-cli-${metrichor_version}

nvm install ${nvm_version}

# npm needs to be installed globally, otherwise I get errors I haven't been able to fix.
# export path to npm and node
export PATH=$PATH:$HOME/.nvm/versions/node/v${nvm_version}/bin/
npm install npm -g

npm install hdf5 -ws:verbose -g

# export path to metrichor commandline agent
export PATH=$PATH:$HOME/metrichor-cli-${metrichor_version}/bin/

# export node path to link to hdf5 module
export NODE_PATH=$HOME/.nvm/versions/node/v${nvm_version}/lib/node_modules/

# change back to current directory
cd ${current_directory}
