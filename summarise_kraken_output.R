#!/usr/bin/env Rscript
args = commandArgs(trailingOnly = TRUE)
# This program creates a frequency table of the taxids.
library(plyr)
input_table = args[1]
output_table = args[2]
print(input_table)
kraken_table = read.table(input_table, sep = "\t")

names(kraken_table) = c("Classified", "Sequence", "Tax_ID", "Seq_length", "LCA_Mapping")

counts <- count(kraken_table, "Tax_ID")

write.table(counts, file=output_table, sep="\t", row.names=FALSE, col.names=FALSE, quote=FALSE)

