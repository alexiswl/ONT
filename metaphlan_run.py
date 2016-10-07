#!/usr/bin/env python

import os

fastq_file = ""
working_directory = "/data/Bioinfo/bioinfo-proj-alexis/MGRG/"
metaphlan_scripts_directory = "~/metaphlan/"
metaphlan_directory = working_directory + "metaphlan/"
fastq_file = ""
classify_output = metaphlan_directory + "classified_output.txt"

# Step 1 Classification

if not os.path.isdir(metaphlan_directory):
    os.mkdir(metaphlan_directory)

metaphlan_classify_command_options = []
metaphlan_classify_command_options.append("--blastdb blastdb/mpa")
metaphlan_classify_command_options.append("--nproc 5")
metaphlan_classify_command_options.append("--blastout")
metaphlan_classify_command = "metaphlan.py %s %s %s" % (' '.join(metaphlan_classify_command_options),
                                                        fastq_file, classify_output)

# Step 22 GraPhlAn visualisation of single and multiple samples


if not os.path.isdir()