#!/usr/bin/env python

from Bio import SeqIO
from operator import attrgetter
import os
import itertools
import commands

# This is a function to test the differences between the reads coming down from metrichor against those
# produced by nanonetcall. This is important to see the importance of whether it is important to send data to
# metrichor, especially for 1D reads.

# With this script I am asking three questions.
# 1. Can we infer the quality of a 2D read presented by nanonet2d by the relationship between the three reads?
# 2. Does this relationship differ between the pass and fail reads of metrichor?
# 3. Does the nanonet2d read differ much from the metrichor 2d read?
# 4. Does the nanonet 1D read differ much from the metrihor 1D read?

main_directory = "/data/Bioinfo/bioinfo-proj-alexis/2016_08_16_E_COLI_R9/"

fasta_directory = main_directory + "fasta/"
fasta_directory_2D = fasta_directory + "2D/2d/"
fasta_directory_fwd = fasta_directory + "2D/fwd/"
fasta_directory_rev = fasta_directory + "2D/rev/"

fastq_directory = main_directory + "fastq/2D/"
fastq_directory_2D = fastq_directory + "pass/2d/"
fastq_directory_fwd = fastq_directory + "pass/fwd/"
fastq_directory_rev = fastq_directory + "pass/rev/"

metrichor_folders = {"2d": fastq_directory_2D, "fwd": fastq_directory_fwd, "rev": fastq_directory_rev}
metrichor_fastq_files = {}
nanonetcall_fasta_files = {}
for type, folder in metrichor_folders.iteritems():
    concatenated_file = folder + "concatenated.fastq"
    os.system("cat %s* > %s" % (folder, concatenated_file))
    metrichor_fastq_files.update({type: concatenated_file})

nanonetcall_folders = {"2d": fasta_directory_2D, "fwd": fasta_directory_fwd, "rev": fasta_directory_rev}
for type, folder in nanonetcall_folders.iteritems():
    concatenated_fasta_file = folder + "concatenated.fasta"
    os.system("cat %s* > %s" % (folder, concatenated_fasta_file))
    nanonetcall_fasta_files.update({type: concatenated_fasta_file})


# Convert fastq file of metrichor into fasta files with correct names.
metrichor_fasta_files = {}
for type, fastq_file in metrichor_fastq_files.iteritems():
    concatenated_fasta_file = fastq_file.split(".")[0] + "concatenated.fasta"
    metrichor_fasta_files.update({type: concatenated_fasta_file})
    input_handle = open(fastq_file, "rU")
    output_handle = open(concatenated_fasta_file, "w+")
    try:
        for record in SeqIO.parse(input_handle, "fastq"):
            output_handle.write(">" + record.description.split()[1] + "\n")
            output_handle.write(str(record.seq) + "\n")
        input_handle.close()
        output_handle.close()
    except ValueError:
        print("No idea why this is happening")

# Sort nanonetcall fasta files
nanonetcall_fasta_files_sorted = {}
for type, fasta_file in nanonetcall_fasta_files.iteritems():
    sorted_fasta_file = fasta_file.split(".")[0] + ".sorted.fasta"
    nanonetcall_fasta_files_sorted.update({type: sorted_fasta_file})
    input_handle = open(fasta_file, "rU")
    output_handle = open(sorted_fasta_file, "w+")
    records = list(SeqIO.parse(input_handle, "fasta"))
    output_fasta = sorted(records, key=attrgetter('id'))
    SeqIO.write(output_fasta, output_handle, "fasta")
    input_handle.close()
    output_handle.close()

# Sort metrichor fasta files
metrichor_fasta_files_sorted = {}
for type, fasta_file in metrichor_fasta_files.iteritems():
    sorted_fasta_file = fasta_file.split(".")[0] + ".sorted.fasta"
    metrichor_fasta_files_sorted.update({type: sorted_fasta_file})
    input_handle = open(fasta_file, "rU")
    output_handle = open(sorted_fasta_file, "w+")
    records = list(SeqIO.parse(input_handle, "fasta"))
    output_fasta = sorted(records, key=attrgetter('id'))
    SeqIO.write(output_fasta, output_handle, "fasta")
    input_handle.close()
    output_handle.close()

# Remove files that are present in only the template or complement set:
_2d_id = []
input_handle = open(nanonetcall_fasta_files_sorted["2d"], "rU")
for record in SeqIO.parse(input_handle, "fasta"):
    _2d_id.append(record.id)
input_handle.close()

input_handle = open(nanonetcall_fasta_files_sorted["fwd"], "rU")
output_handle = open(nanonetcall_fasta_files_sorted["fwd"] + ".tmp", "w+")
for record in SeqIO.parse(input_handle, "fasta"):
    if record.id in _2d_id:
        output_handle.write(">" + record.id + "\n")
        output_handle.write(str(record.seq) + "\n")
input_handle = open(nanonetcall_fasta_files_sorted["rev"], "rU")
output_handle = open(nanonetcall_fasta_files_sorted["rev"] + ".tmp", "w+")
for record in SeqIO.parse(input_handle, "fasta"):
    if record.id in _2d_id:
        output_handle.write(">" + record.id + "\n")
        output_handle.write(str(record.seq.reverse_complement()) + "\n")

os.system("mv %s %s" % (nanonetcall_fasta_files_sorted["fwd"] + ".tmp", nanonetcall_fasta_files_sorted["fwd"]))
os.system("mv %s %s" % (nanonetcall_fasta_files_sorted["rev"] + ".tmp", nanonetcall_fasta_files_sorted["rev"]))


# Determine overall similarity between nanonetcall files
fasta_file_combinations = itertools.combinations(nanonetcall_fasta_files_sorted.values(), 2)


waterman_folder = main_directory + "waterman/"
if not os.path.isdir(waterman_folder):
    os.mkdir(waterman_folder)

intra_comparison_folder = waterman_folder + "intracomparison/"

# Now run the waterman aligner three times (for each different combination)
for (fasta_file_1, fasta_file_2) in fasta_file_combinations:
    combo_directory = intra_comparison_folder + fasta_file_1.split("/")[-1] + "_" + fasta_file_2.split("/")[-1]
    if not os.path.isdir(combo_directory):
        os.mkdir(combo_directory)
    fasta_1_handle = open(fasta_file_1, "rU")
    fasta_2_handle = open(fasta_file_2, "rU")

    fasta_1_rec = list(SeqIO.parse(fasta_1_handle, "fasta"))
    fasta_2_rec = list(SeqIO.parse(fasta_2_handle, "fasta"))

    for afasta, bfasta in zip(fasta_1_rec, fasta_2_rec):
        afile = "tmp_a_file.fasta"
        bfile = "tmp_b_file.fasta"
        a_output_handle = open(afile, "w+")
        SeqIO.write(afasta, a_output_handle, "fasta")
        b_output_handle = open(bfile, "w+")
        SeqIO.write(bfasta, b_output_handle, "fasta")
        a_output_handle.close()
        b_output_handle.close()

        outfile = combo_directory + "waterman" + afasta.id.split("_")[-3] + "_" + afasta.id.split('_')[-2] + ".waterman"
        water_command = "water -asequence %s -sformat1 fasta -bsequence %s -sformat2 fasta -outfile %s -auto" % \
                  (afile, bfile, outfile)
        os.system(water_command)
        os.system("rm %s %s" % (afile, bfile))


# Now split the files based on passed or failed or not performed!
pass_directory = main_directory + "reads/downloads/pass"
_2d_failed_quality_directory = main_directory + "reads/downloads/fail/2D_failed_quality_filters"
_2d_not_performed = main_directory + "reads/downloads/fail/2D_basecall_not_performed"

pass_files = []
_2d_failed_files = []
_2d_not_performed_files = []

for fast5_file in os.listdir(pass_directory):
    pass_files.append(fast5_file.split("_")[-3] + "_" + fast5_file.split("_")[-2])

for fast5_file in os.listdir(_2d_failed_quality_directory):
    _2d_failed_files.append(fast5_file.split("_")[-3] + "_" + fast5_file.split("_")[-2])

for fast5_file in os.listdir(_2d_not_performed):
    _2d_not_performed_files.append(fast5_file.split("_")[-3] + "_" + fast5_file.split("_")[-2])

permutation_folders = [intra_comparison_folder + permutation_folder + "/"
                       for permutation_folder in os.listdir(intra_comparison_folder)
                       if os.path.isdir(permutation_folder)]

for permutation_folder in permutation_folders:
    waterman_pass_folder = permutation_folder + "pass/"
    if not os.listdir(waterman_pass_folder):
        os.mkdir(waterman_pass_folder)
    waterman_failed_quality_folder = permutation_folder + "failed_quality/"
    if not os.listdir(waterman_failed_quality_folder):
        os.mkdir(waterman_failed_quality_folder)
    waterman_not_performed_folder = permutation_folder + "not_performed"
    if not os.listdir(waterman_not_performed_folder):
        os.mkdir(waterman_not_performed_folder)
    other_folder = permutation_folder + "other"
    if not os.listdir(other_folder):
        os.mkdir(other_folder)
    waterman_files = [permutation_folder + waterman_file for waterman_file in permutation_folder]
    for waterman_file in waterman_files:
        if waterman_file in pass_files:
            os.system("mv %s %s" % (waterman_file, waterman_pass_folder))
        elif waterman_file in _2d_failed_files:
            os.system("mv %s %s" % (waterman_file, waterman_failed_quality_folder))
        elif waterman_file in _2d_not_performed_files:
            os.system("mv %s %s" % (waterman_file, waterman_not_performed_folder))
        else:
            os.system("mv %s %s" % (waterman_file, other_folder))

for permutation_folder in permutation_folders:
    porf_folders = [permutation_folder + porf_folder for porf_folder in os.listdir(permutation_folder)
                    if os.path.isdir(porf_folder)]
    for porf_folder in porf_folders:
        input_handle = open(porf_folder + "waterman_stats", "w+")
        waterman_files = [porf_folder + waterman_file for waterman_file in os.listdir(porf_folder)]
        for waterman_file in waterman_files:
            status, score = commands.getstatusoutput(("cat %s | grep '^# Score' | cut -d {0} {0} -f 3" %
                                                      waterman_file).format('"'))
            status, similarity = commands.getstatusoutput(("cat %s | grep '^# Similarity' | cut -d {0} {0} -f 5" %
                                                           waterman_file).format('"'))
            status, identity = commands.getstatusoutput(("cat %s | grep '^# Identity' | cut -d {0} {0} -f 7" %
                                                         waterman_file).format('"'))
            input_handle.write(waterman_file + "\t" + score + "\t" + similarity.strip("()") + "\t" +
                               identity.strip("()"))
        input_handle.close()

# Now to see if there are any differences between the 2D nanonet and the 2D metrichor for the metrichor pass files:
# We will also see if there is any difference between the nanonet template and the metrichor template to
# determine the necessity for metrichor on 1D reads.

# 2D testing
# First ensure that reads are mutually inclusive
pass_id_list = []
input_handle = open(metrichor_fasta_files_sorted["2d"], "rU")
for record in SeqIO.parse(input_handle, "fasta"):
    pass_id_list.append(record.id)
input_handle.close()

input_handle = open(nanonetcall_fasta_files_sorted["2d"], "rU")
output_handle = open(nanonetcall_fasta_files_sorted["2d"] + ".tmp", "w+")

for record in SeqIO.parse(input_handle, "fasta"):
    if record.id in pass_id_list:
        output_handle.write(">" + record.id + "\n")
        output_handle.write(str(record.seq) + "\n")

input_handle.close()
output_handle.close()

os.system("mv %s %s" % (nanonetcall_fasta_files_sorted["2d"] + ".tmp", nanonetcall_fasta_files_sorted["2d"]))

nanonet_id_list = []
input_handle = open(nanonetcall_fasta_files_sorted["2d"], "rU")
for record in SeqIO.parse(input_handle, "fasta"):
    pass_id_list.append(record.id)
input_handle.close()

input_handle = open(metrichor_fasta_files_sorted["2d"], "rU")
output_handle = open(metrichor_fasta_files_sorted["2d"] + ".tmp", "w+")

for record in SeqIO.parse(input_handle, "fasta"):
    if record.id in nanonet_id_list:
        output_handle.write(">" + record.id + "\n")
        output_handle.write(str(record.seq) + "\n")

input_handle.close()
output_handle.close()

os.system("mv %s %s" % (metrichor_fasta_files_sorted["2d"] + ".tmp", metrichor_fasta_files_sorted["2d"]))

# Now another waterman test between the two!
cross_comparison_directory = waterman_folder + "cross_comparison/"
if not os.path.isdir(cross_comparison_directory):
    os.mkdir(cross_comparison_directory)

cross_comparison_directory_2D = waterman_folder + "cross_comparison/2D"
if not os.path.isdir(cross_comparison_directory_2D):
    os.mkdir(cross_comparison_directory_2D)

fasta_1_handle = open(nanonetcall_fasta_files_sorted["2d"], "rU")
fasta_2_handle = open(metrichor_fasta_files_sorted["2d"], "rU")

fasta_1_rec = list(SeqIO.parse(fasta_1_handle, "fasta"))
fasta_2_rec = list(SeqIO.parse(fasta_2_handle, "fasta"))

for afasta, bfasta in zip(fasta_1_rec, fasta_2_rec):
    afile = "tmp_a_file.fasta"
    bfile = "tmp_b_file.fasta"
    a_output_handle = open(afile, "w+")
    SeqIO.write(afasta, a_output_handle, "fasta")
    b_output_handle = open(bfile, "w+")
    SeqIO.write(bfasta, b_output_handle, "fasta")
    a_output_handle.close()
    b_output_handle.close()

    outfile = cross_comparison_directory_2D + afasta.id.split("_")[-3] + "_" + afasta.id.split('_')[-2] + ".waterman"
    water_command = "water -asequence %s -sformat1 fasta -bsequence %s -sformat2 fasta -outfile %s -auto" % \
                    (afile, bfile, outfile)
    os.system(water_command)
    os.system("rm %s %s" % (afile, bfile))

input_handle = open(cross_comparison_directory + "2D_waterman_stats", "w+")
waterman_files = [cross_comparison_directory_2D + waterman_file for waterman_file in os.listdir(cross_comparison_directory_2D)]
for waterman_file in waterman_files:
    status, score = commands.getstatusoutput(
        ("cat %s | grep '^# Score' | cut -d {0} {0} -f 3" % waterman_file).format('"'))
    status, similarity = commands.getstatusoutput(
        ("cat %s | grep '^# Similarity' | cut -d {0} {0} -f 5" % waterman_file).format('"'))
    status, identity = commands.getstatusoutput(
        ("cat %s | grep '^# Identity' | cut -d {0} {0} -f 7" % waterman_file).format('"'))
    input_handle.write(waterman_file + "\t" + score + "\t" + similarity.strip("()") + "\t" + identity.strip("()"))
input_handle.close()



# 1D testing
# First ensure that reads are mutually inclusive
pass_id_list = []
input_handle = open(metrichor_fasta_files_sorted["fwd"], "rU")
for record in SeqIO.parse(input_handle, "fasta"):
    pass_id_list.append(record.id)
input_handle.close()

input_handle = open(nanonetcall_fasta_files_sorted["fwd"], "rU")
output_handle = open(nanonetcall_fasta_files_sorted["fwd"] + ".tmp", "w+")

for record in SeqIO.parse(input_handle, "fasta"):
    if record.id in pass_id_list:
        output_handle.write(">" + record.id + "\n")
        output_handle.write(str(record.seq) + "\n")

input_handle.close()
output_handle.close()

os.system("mv %s %s" % (nanonetcall_fasta_files_sorted["fwd"] + ".tmp", nanonetcall_fasta_files_sorted["fwd"]))

nanonet_id_list = []
input_handle = open(nanonetcall_fasta_files_sorted["fwd"], "rU")
for record in SeqIO.parse(input_handle, "fasta"):
    pass_id_list.append(record.id)
input_handle.close()

input_handle = open(metrichor_fasta_files_sorted["fwd"], "rU")
output_handle = open(metrichor_fasta_files_sorted["fwd"] + ".tmp", "w+")

for record in SeqIO.parse(input_handle, "fasta"):
    if record.id in nanonet_id_list:
        output_handle.write(">" + record.id + "\n")
        output_handle.write(str(record.seq) + "\n")

input_handle.close()
output_handle.close()

os.system("mv %s %s" % (metrichor_fasta_files_sorted["fwd"] + ".tmp", metrichor_fasta_files_sorted["fwd"]))

# Now another waterman test between the two!
cross_comparison_directory_1D = cross_comparison_directory + "1D/"
if not os.path.isdir(cross_comparison_directory_1D):
    os.mkdir(cross_comparison_directory_1D)

fasta_1_handle = open(nanonetcall_fasta_files_sorted["fwd"], "rU")
fasta_2_handle = open(metrichor_fasta_files_sorted["fwd"], "rU")

fasta_1_rec = list(SeqIO.parse(fasta_1_handle, "fasta"))
fasta_2_rec = list(SeqIO.parse(fasta_2_handle, "fasta"))

for afasta, bfasta in zip(fasta_1_rec, fasta_2_rec):
    afile = "tmp_a_file.fasta"
    bfile = "tmp_b_file.fasta"
    a_output_handle = open(afile, "w+")
    SeqIO.write(afasta, a_output_handle, "fasta")
    b_output_handle = open(bfile, "w+")
    SeqIO.write(bfasta, b_output_handle, "fasta")
    a_output_handle.close()
    b_output_handle.close()

    outfile = cross_comparison_directory + afasta.id.split("_")[-3] + "_" + afasta.id.split('_')[-2] + ".waterman"
    water_command = "water -asequence %s -sformat1 fasta -bsequence %s -sformat2 fasta -outfile %s -auto" % \
                    (afile, bfile, outfile)
    os.system(water_command)
    os.system("rm %s %s" % (afile, bfile))


input_handle = open(cross_comparison_directory + "1D_waterman_stats", "w+")
waterman_files = [cross_comparison_directory_1D + waterman_file for waterman_file in os.listdir(cross_comparison_directory_1D)]
for waterman_file in waterman_files:
    status, score = commands.getstatusoutput(
        ("cat %s | grep '^# Score' | cut -d {0} {0} -f 3" % waterman_file).format('"'))
    status, similarity = commands.getstatusoutput(
        ("cat %s | grep '^# Similarity' | cut -d {0} {0} -f 5" % waterman_file).format('"'))
    status, identity = commands.getstatusoutput(
        ("cat %s | grep '^# Identity' | cut -d {0} {0} -f 7" % waterman_file).format('"'))
    input_handle.write(waterman_file + "\t" + score + "\t" + similarity.strip("()") + "\t" + identity.strip("()"))
input_handle.close()