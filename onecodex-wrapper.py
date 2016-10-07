#!/usr/bin/env python

import requests
import os
from Bio import SeqIO
import json
import argparse
import time
import sys
from ete3 import NCBITaxa

ncbi = NCBITaxa()

# Declare global directories
RUN_DIRECTORY = ""
FASTA_DIRECTORY = ""
ONECODEX_DIRECTORY = ""
ONECODEX_OUTPUT_DIRECTORY = ""
SUMMARY_DIRECTORY = ""
TAXA_DIRECTORY = ""
KRONA_DIRECTORY = ""

# Declare global miscellaneous
version = 1.1
RUN_NAME = ""
WATCH = 0
LOGFILE = ""
WATCH_DEFAULT = 800
DATE = time.strftime("%Y_%m_%d")
COMPLETION_FILE = ""
START_TIME = time.time()
SEQUENCES_READ = 0
SEQUENCES_CLASSIFIED = 0
READ_COUNTER = 0

# One Codex admin stuff - Need to export ONECODEX_API_KEY in environment
ONECODEX_SEARCH_HTML = "https://app.onecodex.com/api/v0/search"
ONECODEX_API_KEY = os.environ.get("ONECODEX_API_KEY")
AUTH = requests.auth.HTTPBasicAuth(ONECODEX_API_KEY, "")
TIMEOUT = 20

# Declare ONECODEX STATUS
ONECODEX_DICT = {'Good': 200, 'No api key': 400, 'Invalid api key': 401,
                 'Timeout': 429}


def get_commandline_params():
    help_descriptor = "This is a wrapper for using one_codex on fasta files." + \
                      "This script takes a fasta file and uploads it to onecodex for it to be analysed." + \
                      "The output file is a tab-separated file of read ids and the subsequently assigned tax_id" + \
                      "Only sequences with an assigned tax_id are returned. The file is placed in " + \
                      "<RUN_DIRECTORY>/one_codex"

    parser = argparse.ArgumentParser(description=help_descriptor)
    parser.add_argument('--version', action='version', version="%%(prog)s %s" % str(version))
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
    return args


def set_commandline_params(args):
    global RUN_NAME, RUN_DIRECTORY, FASTA_DIRECTORY
    global WATCH, LOGFILE
    RUN_NAME = args.RUN_NAME
    RUN_DIRECTORY = args.RUN_DIRECTORY
    FASTA_DIRECTORY = args.FASTA_DIRECTORY
    WATCH = args.WATCH
    LOGFILE = args.LOGFILE


def set_directories():
    global RUN_DIRECTORY, FASTA_DIRECTORY, WATCH, LOGFILE, SUMMARY_DIRECTORY
    global ONECODEX_DIRECTORY, ONECODEX_OUTPUT_DIRECTORY, TAXA_DIRECTORY, KRONA_DIRECTORY

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
        LOGFILE = log_directory + DATE + "_" + RUN_NAME + ".onecodex.log"
        general_message = "Log file not defined, using %s" % LOGFILE
        print(general_message)

    ONECODEX_DIRECTORY = RUN_DIRECTORY + "one_codex/"
    if not os.path.isdir(ONECODEX_DIRECTORY):
        os.mkdir(ONECODEX_DIRECTORY)

    ONECODEX_OUTPUT_DIRECTORY = ONECODEX_DIRECTORY + "classification/"
    if not os.path.isdir(ONECODEX_OUTPUT_DIRECTORY):
        os.mkdir(ONECODEX_OUTPUT_DIRECTORY)

    SUMMARY_DIRECTORY = ONECODEX_DIRECTORY + "summary/"
    if not os.path.isdir(SUMMARY_DIRECTORY):
        os.mkdir(SUMMARY_DIRECTORY)

    TAXA_DIRECTORY = ONECODEX_DIRECTORY + "taxa/"
    if not os.path.isdir(TAXA_DIRECTORY):
        os.mkdir(TAXA_DIRECTORY)

    KRONA_DIRECTORY = ONECODEX_DIRECTORY + "krona/"
    if not os.path.isdir(KRONA_DIRECTORY):
        os.mkdir(KRONA_DIRECTORY)


def check_completion_file():
    # Create a text file containing the list of fasta files that have been analysed.
    # Allows one to return to the run if things fail.
    global COMPLETION_FILE
    COMPLETION_FILE = ONECODEX_DIRECTORY + DATE + "_" + RUN_NAME + ".onecodex.completed.txt"
    if not os.path.isfile(COMPLETION_FILE):
        os.system("touch %s" % COMPLETION_FILE)

    fasta_files_old = []
    with open(COMPLETION_FILE, "r") as f:
        for line in f:
            line = line.rstrip()
            fasta_files_old.append(line)
    return fasta_files_old


def start_log():
    logger = open(LOGFILE, 'a+')
    logger.write("The time is %s\n" % time.strftime("%c"))
    logger.write("Reading fasta files from %s \n" % FASTA_DIRECTORY)
    logger.close()


def end_log():
    # Run has been exhausted.
    logger = open(LOGFILE, 'a+')
    end_time = time.time()
    run_time = end_time - START_TIME
    logger.write("Finished one codex analysis in %d seconds.\n" % run_time)
    logger.write("Analysed %d sequences\n" % SEQUENCES_READ)
    logger.write("Classified %d sequences\n" % SEQUENCES_CLASSIFIED)
    logger.close()


def onecodex_wrapper():
    fasta_files_old = check_completion_file()
    run_exhausted = False

    # Create for loop, searching for created 1D fasta files.

    while not run_exhausted:
        fasta_files = []
        patience_counter = 0
        while len(fasta_files) == 0:
            fasta_files = [FASTA_DIRECTORY + filename for filename in os.listdir(FASTA_DIRECTORY)
                           if filename.endswith((".fa", ".fasta", ".fna")) and filename not in fasta_files_old]
            if len(fasta_files) != 0:
                break
            # Important to transfer the oldest files first.
            fasta_files.sort(key=lambda x: os.path.getmtime(x))

            if WATCH < patience_counter:
                run_exhausted = True
                return run_exhausted
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
        completed_fasta_files = run_onecodex_pipeline(fasta_files)

        for fasta_file in completed_fasta_files:
            fasta_files_old.append(fasta_file)


def run_onecodex(fasta_sequences, onecodex_file):
    global SEQUENCES_CLASSIFIED, SEQUENCES_READ
    for fasta_sequence in fasta_sequences:
        name, sequence = fasta_sequence.id, str(fasta_sequence.seq)
        payload = {'sequence': sequence}
        try:
            r = requests.post(ONECODEX_SEARCH_HTML, payload, auth=AUTH, timeout=TIMEOUT)
        except requests.exceptions.ConnectionError:
            print "Connection error!"
            print "This is the culprit read %s" % fasta_sequence
            continue
        except requests.exceptions.SSLError:
            print "SSL Error"
            print "This is the culprit read %s" % fasta_sequence
            continue
        if r.status_code != ONECODEX_DICT['Good']:
            if r.status_code == ONECODEX_DICT['No api key']:
                error_message = "No api key has been provided. Please define your" + \
                                "ONECODEX_API_KEY in your environment. Exiting"
                sys.exit(error_message)
            if r.status_code == ONECODEX_DICT['Invalid api key']:
                error_message = "Invalid api key has been provided. Exiting."
                sys.exit(error_message)
            if r.status_code == ONECODEX_DICT['Timeout']:
                warning_message = "Onecodex has timed out. Check connection."
                print warning_message
            else:
                logger = open(LOGFILE, 'a+')
                logger.write("Unknown error %s" % r.status_code)
                logger.close()
        result = json.loads(r.text)
        tax_id = result['tax_id']
        SEQUENCES_READ += 1
        if tax_id != 0:
            SEQUENCES_CLASSIFIED += 1
            onecodex_fh = open(onecodex_file, 'a+')
            onecodex_fh.write(name + "\t" + str(tax_id) + "\n")
            onecodex_fh.close()


def run_summary(onecodex_file, summary_file):
    summary_command = "summarise_onecodex_output.R %s %s" \
                      % (onecodex_file, summary_file)
    os.system(summary_command)


def run_taxa(summary_file, taxa_file):
    taxa_file_h = open(taxa_file, 'a+')
    with open(summary_file, "r") as f:
        # Convert tax_ids to lineage
        for line in f:
            try:
                line = line.rstrip()
                tax_id, freq = line.split("\t")
                lineage = ncbi.get_lineage(tax_id)
                names = ncbi.get_taxid_translator(lineage)
                lineage_names = [names[taxid] for taxid in lineage]
                taxa_file_h.write(freq + "\t" + "\t".join(lineage_names[1:]) + "\n")
            except ValueError:
                print "Error classifying tax_id %s." % tax_id
    taxa_file_h.close()


def run_onecodex_pipeline(fasta_files):
    completed_fasta_files = []
    # Run one codex on the set of fasta files.
    for fasta_file in fasta_files:
        time_suffix = str(time.strftime("%Y-%m-%d-%H-%M-%S"))
        fasta_sequences = SeqIO.parse(open(fasta_file), 'fasta')
        onecodex_file = ONECODEX_OUTPUT_DIRECTORY + RUN_NAME + "_" + time_suffix + ".onecodex.txt"
        summary_file = SUMMARY_DIRECTORY + RUN_NAME + "_" + time_suffix + ".onecodex.table.txt"
        taxa_file = TAXA_DIRECTORY + RUN_NAME + "_" + time_suffix + ".onecodex.taxa.txt"
        krona_file = KRONA_DIRECTORY + RUN_NAME + "_" + time_suffix + ".krona.html"

        # Run the fasta file through one-codex
        run_onecodex(fasta_sequences, onecodex_file)

        # Onecodex file may not have been written to if no fasta file matched.
        if not os.path.isfile(onecodex_file):
            continue

        # Create a summary of the output
        run_summary(onecodex_file, summary_file)

        # Convert into taxa
        run_taxa(summary_file, taxa_file)

        # Run krona
        run_krona(krona_file)

        # Append and update completed files with fasta file
        completion_file_h = open(COMPLETION_FILE, 'a+')
        completion_file_h.write(fasta_file + "\n")
        completed_fasta_files.append(fasta_file)

    return completed_fasta_files


def run_krona(krona_file):
    # Generate time-stamp for plot.
    running_m, running_s = divmod(time.time() - START_TIME, 60)
    running_h, running_m = divmod(running_m, 60)

    # Run krona on all the taxa files in the taxa directory.
    ktImportCommands = []
    ktImportCommands.append("-o %s" % krona_file)
    ktImportCommands.append("-n %s_%d:%02d:%02d" % (RUN_NAME, running_h, running_m, running_s))
    ktImportCommands.append("-c")
    for taxa_file in os.listdir(TAXA_DIRECTORY):
        if taxa_file.endswith(".taxa.txt"):
            ktImportCommands.append(TAXA_DIRECTORY + taxa_file)
    krona_command = "ktImportText %s" % ' '.join(ktImportCommands)
    logger = open(LOGFILE, 'a+')
    logger.write("Commencing Krona command.\n")
    logger.write("The command is: %s \n" % krona_command)
    os.system(krona_command)


def main():
    # Get arguments from the commandline
    args = get_commandline_params()

    # Set the arguments from the commandline
    set_commandline_params(args)

    # Set directories:
    set_directories()
    
    # Start log
    start_log()

    # Run onecodex
    onecodex_wrapper()

    # Finish log
    end_log()

main()
