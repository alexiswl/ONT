#!/usr/bin/env python

import requests
import os
from Bio import SeqIO
import json
import argparse
import time
import sys

help_descriptor = "This is a wrapper for using one_codex on fasta files." + \
                  "This script takes a fasta file and uploads it to onecodex for it to be analysed." + \
                  "The output file is a tab-separated file of read ids and the subsequently assigned tax_id" + \
                  "Only sequences with an assigned tax_id are returned. The file is placed in " + \
                  "<RUN_DIRECTORY>/one_codex"

parser = argparse.ArgumentParser(description=help_descriptor)
parser.add_argument('--version', action='version', version="%(prog)s 1.0")
parser.add_argument("--run_name", nargs='?', dest="RUN_NAME", type=str,
                    help="What do you want the tab delimited file to be called.?",
                    required=True)
parser.add_argument("--run_directory", nargs='?', dest="RUN_DIRECTORY", type=str,
                    help="This is generally the parent folder of the fasta folder.",
                    required=True)
parser.add_argument("--fasta_directory", nargs="?", dest="FASTA_DIRECTORY", type=str,
                    help="This is the directory in which fasta files are placed in to.")

parser.add_argument("--watch", nargs='?', dest="WATCH", type=int,
                    help="The time (seconds) allowed with no new fasta files" +
                         "entering the fasta directory before exiting the script. Default set at 800")
parser.add_argument("--logfile", nargs='?', dest="LOGFILE", type=str,
                    help="This is the file that some general notes are printed to. If not specified," +
                         "the file will be RUN_DIRECTORY/log/<run_name>.onecodex.log")
args = parser.parse_args()

RUN_NAME = args.RUN_NAME
RUN_DIRECTORY = args.RUN_DIRECTORY
FASTA_DIRECTORY = args.FASTA_DIRECTORY
WATCH = args.WATCH
LOGFILE = args.LOGFILE

# Defaults
WATCH_DEFAULT = 800
date = time.strftime("%Y_%m_%d")
GOOD_ONECODEX_STATUS = 200

# Checking to ensure that the run directory exists
if not os.path.isdir(RUN_DIRECTORY):
    error_message = "Error: cannot locate or find fasta directory %s" % RUN_DIRECTORY
    sys.exit(error_message)
RUN_DIRECTORY = os.path.abspath(RUN_DIRECTORY) + "/"

# Checking to ensure that the fasta directory exists
if FASTA_DIRECTORY:
    if not os.path.isdir(FASTA_DIRECTORY):
        error_message = "Error: cannot locate or find fasta directory %s" % FASTA_DIRECTORY
        sys.exit(error_message)
if not FASTA_DIRECTORY:
    FASTA_DIRECTORY = RUN_DIRECTORY + "fasta"
FASTA_DIRECTORY = os.path.abspath(FASTA_DIRECTORY) + "/"

if not WATCH:
    WATCH = WATCH_DEFAULT
    general_message = "Watch option not defined. Using %s" % WATCH_DEFAULT
    print(general_message)

# Create the log file
if LOGFILE:
    if not os.path.isfile(LOGFILE):
        error_message = "Log file specifed but does not exist."
        sys.exit(error_message)
else:
    log_directory = RUN_DIRECTORY + "log/"
    if not os.path.isdir(log_directory):
        os.makedirs(log_directory)
    LOGFILE = log_directory + date + "_" + RUN_NAME + ".onecodex.log"
    general_message = "Log file not defined, using %s" % LOGFILE
    print(general_message)

# Prime run
run_exhausted = 0
fasta_files_old = []
fasta_files = []
sequences_read = 0
sequences_classified = 0
patience_counter = 0

# One Codex admin stuff
ONECODEX_SEARCH_HTML = "https://app.onecodex.com/api/v0/search"
ONECODEX_API_KEY = os.environ.get("ONECODEX_API_KEY")
auth = requests.auth.HTTPBasicAuth(ONECODEX_API_KEY, "")
timeout = 20


one_codex_directory = RUN_DIRECTORY + "one_codex/"
if not os.path.isdir(one_codex_directory):
    os.mkdir(one_codex_directory)

output_file = one_codex_directory + date + "_" + RUN_NAME + ".onecodex"

start_time = time.time()
logger = open(LOGFILE, 'a+')
logger.write("The time is %s\n" % time.strftime("%c"))
logger.write("Reading fasta files from %s \n" % FASTA_DIRECTORY)
logger.write("Writing to: %s\n" % output_file)
logger.close()

# Create for loop, searching for created 1D fasta files.
while not run_exhausted:
    while len(fasta_files) == 0:
        fasta_files = [FASTA_DIRECTORY + filename for filename in os.listdir(FASTA_DIRECTORY)
                       if filename.endswith((".fa", ".fasta", ".fna")) and filename not in fasta_files_old]
        if len(fasta_files) != 0:
            break

        if WATCH < patience_counter:
            run_exhausted = True
            break
        # No? Take a minute sleep.
        if patience_counter != 0:
            abstinence_message = "No fast5 files found in the last %d seconds.\n" % patience_counter
            sleeping_message = "Waiting 60 seconds, breaking in {0:d} if no more reads created.\n" \
                .format(WATCH - patience_counter)
            logger = open(LOGFILE, 'a+')
            print(abstinence_message)
            print(sleeping_message)
            logger.write(abstinence_message + "\n")
            logger.write(sleeping_message + "\n")
        time.sleep(60)
        patience_counter += 60

    # Out of the while loop, either fast5 files have been found or run is exhausted.
    patience_counter = 0  # Must be consecutive minute sleeps to exhaust the run.

    # Run one codex on the set of fasta files.
    for fasta_file in fasta_files:
        fasta_sequences = SeqIO.parse(open(fasta_file), 'fasta')
        output = open(output_file, 'a+')
        for fasta in fasta_sequences:
            name, sequence = fasta.id, str(fasta.seq)
            payload = {'sequence':sequence}
            r = requests.post(ONECODEX_SEARCH_HTML, payload, auth=auth, timeout=timeout)
            if r.status_code != GOOD_ONECODEX_STATUS:
                if r.status_code == 400:
                    sys.exit('The One Codex API key was not provided')
                elif r.status_code == 401:
                    sys.exit('The One Codex API key provided was invalid')
                else:
                  continue

            result = json.loads(r.text)
            tax_id = result['tax_id']
            sequences_read += 1
            if tax_id != 0:
                sequences_classified += 1
                output.write(name + "\t" + str(tax_id) + "\n")
        fasta_files_old.append(fasta_file)
        output.close()
    # Re-enter for loop
    fasta_files = []
# Run has been exhausted.
output.close()

logger = open(LOGFILE, 'a+')
end_time = time.time()
run_time = end_time - start_time
logger.write("Finished one codex analysis in %d seconds.\n" % run_time)
logger.write("Analysed %d sequences\n" % sequences_read)
logger.write("Classified %d sequences\n" % sequences_classified)
