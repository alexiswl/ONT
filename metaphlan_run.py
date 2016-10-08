#!/usr/bin/env python

import os

fastq_file = ""
working_directory = "/data/Bioinfo/bioinfo-proj-alexis/MGRG/"
metaphlan_directory = working_directory + "metaphlan/"
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
os.system(metaphlan_classify_command)
# Step 2 GraPhlAn visualisation of single and multiple samples
# Part 1 Metaphlan to Graphlan
tree_file = classify_output + ".tree.txt"
annot_file = classify_output + ".annot.txt"

meta_to_graph_command_options = []
meta_to_graph_command_options.append("--tree_file %s" % tree_file)
meta_to_graph_command_options.append("--annot_file %s" % annot_file)
meta_to_graph_command = "metaphlan2graphlan.py %s %s" % (' '.join(meta_to_graph_command_options), classify_output)
os.system(meta_to_graph_command)

# Part 2 Graphlan annotation
xml_file = classify_output + ".xml"
graphlan_annotation_command_options = []
graphlan_annotation_command_options.append("--annot %s" % annot_file)
graphlan_annotation_command_options.append("%s" % tree_file)

graphlan_annotation_command = "graphlan_annotate.py %s %s" % \
                              (' '.join(graphlan_annotation_command_options), xml_file)
os.system(graphlan_annotation_command)
# Part 3 Graphlan output
output_png = classify_output + ".png"
graphlan_command_options = []
graphlan_command_options.append("--dpi 200")
graphlan_command_options.append("%s" % xml_file)
graphlan_command = "graphlan.py %s %s" % (' '.join(graphlan_command_options), output_png)

os.system(graphlan_command)