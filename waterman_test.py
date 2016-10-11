#!/usr/bin/env python

from Bio import SeqIO
from operator import attrgetter
import os
# This is a function to test the differences between the reads coming down from metrichor against those
# produced by nanonetcall. This is important to see the importance of whether it is important to send data to
# metrichor, especially for 1D reads.

main_directory = "/data/Bioinfo/bioinfo-proj-alexis/2016_08_16_E_COLI_R9/"
fastq_file = main_directory + "fastq/2016-10-03_E_COLI_R9.fastq"
metrichor_fasta = main_directory + "metichor.fasta"
fasta_file = main_directory + "all_fasta.fasta"
nanonet_fasta = fasta_file + ".nanonet.fasta"

# Turn fastq file into fasta file
input_handle = open(fastq_file, "rU")
output_handle = open(metrichor_fasta, "w+")

for record in SeqIO.parse(input_handle, "fastq"):
    output_handle.write(">" + record.description.split()[1] + "\n")
    output_handle.write(str(record.seq) + "\n")	
input_handle.close()
output_handle.close()

# Grab ids of metrichor file
met_id = []
input_handle = open(metrichor_fasta, "rU")
for record in SeqIO.parse(input_handle, "fasta"):
    met_id.append(record.id)
input_handle.close()


# Make a "pass" fasta file.
pass_reads = []
both_id = []
output_handle = open(nanonet_fasta, "w+")
input_handle = open(fasta_file, "rU")
for record in SeqIO.parse(input_handle, "fasta"): 
    if record.id in met_id:	
        pass_reads.append(record)
	both_id.append(record.id)
input_handle.close()
SeqIO.write(pass_reads, output_handle, "fasta")
output_handle.close()


# Make sure that metrichor reads are also in fasta reads:
pass_reads = []
metrichor_filtered = metrichor_fasta + "filtered.fasta"
output_handle = open(metrichor_filtered, "w+")
input_handle = open(metrichor_fasta, "rU")
for record in SeqIO.parse(metrichor_fasta, "fasta"):
	if record.id in both_id:
		pass_reads.append(record)
input_handle.close()
SeqIO.write(pass_reads, output_handle, "fasta")
output_handle.close()

# Sort both files:
fastx_files = (nanonet_fasta, fastq_file)
fasta_file_sorted = nanonet_fasta + ".sorted.fasta"
fastq_file_sorted = metrichor_filtered + ".sorted.fasta"
    
input_handle = open(nanonet_fasta, "rU")
output_handle = open(fasta_file_sorted, "w+")
records = list(SeqIO.parse(input_handle, "fasta"))
output_fasta = sorted(records, key=attrgetter('id'))
SeqIO.write(output_fasta, output_handle, "fasta")
input_handle.close()
output_handle.close()


input_handle = open(metrichor_filtered, "rU")
output_handle = open(fastq_file_sorted, "w+")
records = list(SeqIO.parse(input_handle, "fasta"))
output_fasta = sorted(records, key=attrgetter('id'))
SeqIO.write(output_fasta, output_handle, "fasta")
input_handle.close()
output_handle.close()

met_handle = open(fastq_file_sorted, "rU")
nanonet_handle = open(fasta_file_sorted, "rU")

met_rec = list(SeqIO.parse(met_handle, "fasta"))
nanonet_rec = list(SeqIO.parse(nanonet_handle, "fasta"))
waterman_directory = main_directory + "waterman/"

if not os.path.isdir(waterman_directory):
    os.mkdir("waterman")

for a, b in zip(met_rec, nanonet_rec):
   afile = "tmp_met_file.fasta"
   bfile = "tmp_nanonet_file.fasta"
   a_output_handle = open(afile, "w+")
   SeqIO.write(a, a_output_handle, "fasta")
   a_output_handle.close()
   b_output_handle = open(bfile, "w+")
   SeqIO.write(b, b_output_handle, "fasta")
   b_output_handle.close()
   outfile = waterman_directory + "ch" + a.id.split('_')[-2] + "read" + a.id.split('_')[-3]
   command = "water -asequence %s -sformat1 fasta -bsequence %s -sformat2 fasta -outfile %si -auto" % (afile, bfile, outfile)
   os.system(command)

