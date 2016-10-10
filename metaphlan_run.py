#!/usr/bin/env python

import os

fastq_file = "/data/Bioinfo/bioinfo-proj-alexis/MGRG/fastq/mgrg_MinION.fastq"
working_directory = "/data/Bioinfo/bioinfo-proj-alexis/MGRG/"
metaphlan_directory = working_directory + "metaphlan/"
run_name = metaphlan_directory + "MGRG_MinION"
classified_output = run_name + ".classified_output.txt"

# Step 1 Classification

if not os.path.isdir(metaphlan_directory):
    os.mkdir(metaphlan_directory)

metaphlan_classify_command_options = []
metaphlan_classify_command_options.append("--nproc 5")
metaphlan_classify_command_options.append("--input_type fastq")
metaphlan_classify_command_options.append("--blastdb blastdb/mpa")

metaphlan_classify_command = "metaphlan.py %s %s > %s" % (' '.join(metaphlan_classify_command_options),
                                                          fastq_file, run_name)
os.system(metaphlan_classify_command)
# Step 2 GraPhlAn visualisation of single and multiple samples
# Part 1 Metaphlan to Graphlan
tree_file = run_name + ".tree.txt"
annot_file = run_name + ".annot.txt"

meta_to_graph_command_options = []
meta_to_graph_command_options.append("--tree_file %s" % tree_file)
meta_to_graph_command_options.append("--annot_file %s" % annot_file)
meta_to_graph_command = "metaphlan2graphlan.py %s %s" % (' '.join(meta_to_graph_command_options), run_name)
os.system(meta_to_graph_command)

# Part 2 Graphlan annotation
xml_file = run_name + ".xml"
graphlan_annotation_command_options = []
graphlan_annotation_command_options.append("--annot %s" % annot_file)
graphlan_annotation_command_options.append("%s" % tree_file)

graphlan_annotation_command = "graphlan_annotate.py %s %s" % \
                              (' '.join(graphlan_annotation_command_options), xml_file)
os.system(graphlan_annotation_command)

# Part 3 Graphlan output
output_png = run_name + ".png"
graphlan_command_options = []
graphlan_command_options.append("--dpi 200")
graphlan_command_options.append("%s" % xml_file)
graphlan_command = "graphlan.py %s %s" % (' '.join(graphlan_command_options), output_png)

os.system(graphlan_command)