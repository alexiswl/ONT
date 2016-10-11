#!/usr/bin/python env

import h5py
import os

# This script breaks down the distribution of the output datasets in each of the hdf5 files.
datasets = {}
datasets['basecall_1D_summary_dataset'] = '/Analyses/Basecall_1D_000/Summary'
datasets['event_detection_dataset'] = '/Analyses/EventDetection_000/Summary'
datasets['calibration_summary_dataset'] = '/Analyses/Calibration_Strand_000/Summary'
datasets['segment_linear_dataset'] = '/Analyses/Segment_Linear_000/Summary'
datasets['basecall_2D_summary_dataset'] = '/Analyses/Basecall_2D_000/Summary'
datasets['hairpin_summary_dataset'] = '/Analyses/Hairpin_Split_000/Summary'

main_folder = "/data/Bioinfo/bioinfo-proj-alexis/2016_08_16_E_COLI_R9/"
folders = [name for name in os.listdir(main_folder) if os.path.isdir(os.path.join(main_folder, name))]

for folder in folders:
    folder_file = folder + "breakdown.txt"
    folder_file_h = open(folder_file, "w+")

    for fast5_file in os.listdir(folder):
        if not os.path.isfile(fast5_file) or not fast5_file.endswith(".fast5"):
            continue
        # Check to ensure that the file is not corrupt.
        try:
            f = h5py.File(fast5_file, 'r')
        except IOError:
            folder_file_h.write("corrupted_file")
            continue
        # File not corrupt, move to folders accordingly.
        for key, value in datasets.iteritems():
            try:
                folder_file_h.write(f[value].attrs.values()[0])
            except KeyError:
                folder_file_h.write("Key Error")
        folder_file_h.write("\n")
    folder_file_h.close()

