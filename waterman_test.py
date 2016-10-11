#!/usr/bin/env python

from Bio import SeqIO

# This is a function to test the differences between the reads coming down from metrichor against those
# produced by nanonetcall. This is important to see the importance of whether it is important to send data to
# metrichor, especially for 1D reads.

main_directory = "/data/Bioinfo/bioinfo-proj-alexis/2016_08_16_E_COLI_R9/"
fastq_file = main_directory + "fastq/2016-10-03_E_COLI_R9.fastq"
fasta_file = main_directory + "all_fasta"
pass_fasta = main_directory + fasta_file + ".pass.fasta"

# Grab ids of fastq file
fastq_id = []
input_handle = open(fastq_file, "rU")
for record in SeqIO.parse(input_handle, "fastq"):
    fastq_id.append(record.id)
input_handle.close()

# Make a "pass" fasta file.
output_handle = open(pass_fasta, "w")
input_handle = open(fasta_file, "rU")
for record in SeqIO.parse(input_handle, "fasta"):
    if record.id in fastq_id:
        SeqIO.write(record, output_handle, "fasta")
input_handle.close()
output_handle.close()

# Sort both files:
fastx_files = (fasta_file, fastq_file)
fasta_file_sorted = fasta_file + ".sorted"
fastq_file_sorted = fastq_file + ".sorted"
for fastx_file in fastx_files:
    input_handle = open(fastx_file, "rU")
    output_handle = open(fastx_file + ".sorted", "w")
    records = list(SeqIO.parse(input_handle, "fasta"))
    records.sort(key=lambda record: record.id())
    SeqIO.write(records, output_handle, "fasta")
