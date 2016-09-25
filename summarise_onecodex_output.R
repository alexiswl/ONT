#!/usr/bin/env Rscript
args = commandArgs(trailingOnly = TRUE)
# This program creates a frequency table of the taxids.
library(plyr)
input_table = args[1]
output_table = args[2]
onecodex_table = read.table(input_table, sep = "\t")

names(onecodex_table) = c("read_name", "Tax_ID")

counts <- count(onecodex_table, "Tax_ID")

write.table(counts, file=output_table, sep="\t", row.names=FALSE, col.names=FALSE, quote=FALSE)

