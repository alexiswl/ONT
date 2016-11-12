#!/usr/bin/env python

import os
import time
import argparse
import sys
import commands

from ete3 import NCBITaxa
ncbi = NCBITaxa()


# This script is designed to take in a fasta directory
# that is continuously producing fasta files coming off a MinION run
# A plot is then created of the metagenomic distribution of the sample.
# This plot is updated as more fasta files come through

# Declare global directories
RUN_DIRECTORY = ""
FASTA_DIRECTORY = ""
KRAKEN_DATABASE = ""
KRAKEN_DIRECTORY = ""
KRAKEN_OUTPUT_DIRECTORY = ""
KRAKEN_FREQ_DIRECTORY = ""
KRAKEN_TAXA_DIRECTORY = ""
KRONA_DIRECTORY = ""

# Declare global miscellaneous
version = 1.1
THREAD_COUNT = 0
THREAD_COUNT_DEFAULT = 4
DATE_PREFIX = time.strftime("%Y_%m_%d")
START_TIME = time.time()
WATCH_DEFAULT = 800
RUN_NAME = ""
LOGFILE = ""
COMPLETION_FILE = ""
WATCH = 0
IS_1D = False

def get_commandline_params():
    help_descriptor = "This is a script designed to take a fasta directory as input and produce a set" + \
                      "of output plots." + \
                      "Plots continuously created until no new fasta files are created for 'watch' time."

    parser = argparse.ArgumentParser(description=help_descriptor)

    parser.add_argument('--version', action='version', version="%%(prog)s %s" % str(version))
    parser.add_argument("--run_name", nargs='?', dest="RUN_NAME", type=str,
                        help="What name would you like to place into the Krona html files.",
                        required=True)
    parser.add_argument("--run_directory", nargs='?', dest="RUN_DIRECTORY", type=str,
                        help="This is the working directory." +
                             "A folder called kraken will be written into this directory.",
                        required=True)
    parser.add_argument("--fasta_directory", nargs='?', dest="FASTA_DIRECTORY", type=str,
                        help="The directory with the fasta files within them. If not specified, this will be:" +
                             "<run_directory>/fasta")
    parser.add_argument("--1D", action='store_true', dest="IS_1D", default=False,
                        help="Fasta directory is split between 1D and 2D reads. Did nanonet use 1D or 2D nanonet call?")
    parser.add_argument("--kraken_database", nargs='?', dest="KRAKEN_DATABASE", type=str,
                        help="The database used in kraken", required=True)
    parser.add_argument("--watch", nargs='?', dest="WATCH", type=int,
                        help="How long would you like to wait for a new fasta file to arrive before exiting script.")
    parser.add_argument("--thread_count",  nargs='?', dest="THREAD_COUNT", type=int,
                        help="The number of threads used to run kraken. If not specified, this will default to 4.")
    parser.add_argument("--logfile", nargs='?', dest="LOGFILE", type=str,
                        help="Append to an existing log file, otherwise will be written to <run_directory>/log/")

    args = parser.parse_args()
    return args


def set_commandline_variables(args):
    global RUN_NAME, RUN_DIRECTORY, FASTA_DIRECTORY, KRAKEN_DATABASE, WATCH, IS_1D
    global THREAD_COUNT, LOGFILE, KRAKEN_DIRECTORY, KRONA_DIRECTORY, COMPLETION_FILE
    # Assign inputs
    RUN_NAME = args.RUN_NAME
    RUN_DIRECTORY = args.RUN_DIRECTORY
    FASTA_DIRECTORY = args.FASTA_DIRECTORY
    KRAKEN_DATABASE = args.KRAKEN_DATABASE
    THREAD_COUNT = args.THREAD_COUNT
    WATCH = args.WATCH
    LOGFILE = args.LOGFILE
    IS_1D = args.IS_1D


def set_directories():
    global RUN_DIRECTORY, FASTA_DIRECTORY, KRAKEN_DATABASE, WATCH
    global THREAD_COUNT, LOGFILE, COMPLETION_FILE, KRAKEN_DIRECTORY, KRONA_DIRECTORY
    global KRAKEN_OUTPUT_DIRECTORY, KRAKEN_TAXA_DIRECTORY, KRAKEN_FREQ_DIRECTORY

    # Set run directory
    if not os.path.isdir(RUN_DIRECTORY):
        error_message = "Error: Run directory defined but does not exist."
        sys.exit(error_message)
    RUN_DIRECTORY = os.path.abspath(RUN_DIRECTORY) + "/"

    # Configure optional arguments
    if FASTA_DIRECTORY:
        if not os.path.isdir(FASTA_DIRECTORY):
            error_message = "Error: Fasta directory specified but does not exist."
            sys.exit(error_message)
    else:
        FASTA_DIRECTORY = RUN_DIRECTORY + "fasta/"
        if not os.path.isdir(FASTA_DIRECTORY):
            os.mkdir(FASTA_DIRECTORY)
        if IS_1D:
            FASTA_DIRECTORY += "1D/"
        else:
            FASTA_DIRECTORY += "2D/"
        if not os.path.isdir(FASTA_DIRECTORY):
            os.mkdir(FASTA_DIRECTORY)
    FASTA_DIRECTORY = os.path.abspath(FASTA_DIRECTORY) + "/"

    if not os.path.isdir(KRAKEN_DATABASE):
        error_message = "Error: Kraken database - invalid directory"
        sys.exit(error_message)
    KRAKEN_DATABASE = os.path.abspath(KRAKEN_DATABASE) + "/"

    if not THREAD_COUNT:
        THREAD_COUNT = THREAD_COUNT_DEFAULT
        general_message = "Thread count not defined, defaulting to %d" % THREAD_COUNT_DEFAULT
        print(general_message)
    if not WATCH:
        WATCH = WATCH_DEFAULT
        general_message = "Watch not defined, defaulting to %d" % WATCH_DEFAULT
        print(general_message)

    if LOGFILE:
        if not os.path.isdir(LOGFILE):
            error_message = "Logfile defined but does not exist."
            sys.exit(error_message)
        LOGFILE = os.path.abspath(LOGFILE)
    else:
        log_directory = RUN_DIRECTORY + "log/"
        if not os.path.isdir(log_directory):
            os.mkdir(log_directory)
        LOGFILE = log_directory + DATE_PREFIX + "_" + RUN_NAME + ".kraken.log"

    KRAKEN_DIRECTORY = RUN_DIRECTORY + "kraken/"

    if not os.path.isdir(KRAKEN_DIRECTORY):
        os.mkdir(KRAKEN_DIRECTORY)

    KRAKEN_OUTPUT_DIRECTORY = KRAKEN_DIRECTORY + "kraken_output/"
    KRAKEN_TAXA_DIRECTORY = KRAKEN_DIRECTORY + "taxa/"
    KRAKEN_FREQ_DIRECTORY = KRAKEN_DIRECTORY + "freq/"

    if not os.path.isdir(KRAKEN_OUTPUT_DIRECTORY):
        os.mkdir(KRAKEN_OUTPUT_DIRECTORY)

    if not os.path.isdir(KRAKEN_FREQ_DIRECTORY):
        os.mkdir(KRAKEN_FREQ_DIRECTORY)

    if not os.path.isdir(KRAKEN_TAXA_DIRECTORY):
        os.mkdir(KRAKEN_TAXA_DIRECTORY)

    KRONA_DIRECTORY = KRAKEN_DIRECTORY + "krona/"
    if not os.path.isdir(KRONA_DIRECTORY):
        os.mkdir(KRONA_DIRECTORY)

    # Create a text file containing the list of fasta files that have been analysed.
    # Allows one to return to the run if things fail.
    COMPLETION_FILE = KRAKEN_DIRECTORY + RUN_NAME + "_" + DATE_PREFIX + ".kraken.completed.txt"


def start_log():
    logger = open(LOGFILE, 'a+')
    logger.write("Commencing real-time krona plots of MinION data\n")
    logger.write("The input command is: %s \n" % ' '.join(sys.argv[:]))
    # Write out what has been assigned to the log file:
    logger.write("The run directory is: %s\n" % RUN_DIRECTORY)
    logger.write("The kraken database is: %s\n" % KRAKEN_DATABASE)
    logger.close()


def end_log():
    logger = open(LOGFILE, 'a+')
    logger.write("Kraken script has completed.\n")
    logger.close()


def check_completion_file():
    if not os.path.isfile(COMPLETION_FILE):
        os.system("touch %s" % COMPLETION_FILE)

    fasta_files_old = []
    with open(COMPLETION_FILE, "r") as f:
        for line in f:
            line = line.rstrip()
            fasta_files_old.append(line)
    return fasta_files_old


def kraken_wrapper():
    # Set up for the kraken/krona script
    run_exhausted = False
    fasta_files_old = check_completion_file()

    # While loop starts here
    while not run_exhausted:
        patience_counter = 0  # must be consistent absence of reads
        fasta_files = []
        while len(fasta_files) == 0:
            # Find the new fasta files
            for filename in os.listdir(FASTA_DIRECTORY):
                if filename.endswith((".fasta", ".fna", ".fa")) and FASTA_DIRECTORY + filename not in fasta_files_old:
                    fasta_files.append(FASTA_DIRECTORY + filename)

            if len(fasta_files) != 0:
                break

            # Didn't pick anything up...
            # Have we exceeded the number of mini-sleeps?
            if patience_counter > WATCH:
                run_exhausted = True
                return run_exhausted

            # No? Take a minute sleep.
            if patience_counter != 0:
                print "No fasta files found in the last %d seconds.\n" % patience_counter
                print "Waiting 60 seconds, breaking in %d if no more fasta files generated.\n" \
                      % (WATCH - patience_counter)
            time.sleep(60)
            patience_counter += 60

        # Out of while loop, fast5 files found or run is exhausted.
        completed_fasta_files = run_kraken_pipeline(fasta_files)
        completion_h = open(COMPLETION_FILE, 'a+')
        for fasta_file in completed_fasta_files:
            fasta_files_old.append(fasta_file)
            completion_h.write(fasta_file)
            completion_h.write("\n")
        completion_h.close()


def run_kraken_pipeline(fasta_files):

    # Set the output files for each condition.
    time_suffix = str(time.strftime("%Y-%m-%d-%H-%M-%S"))
    kraken_output = KRAKEN_OUTPUT_DIRECTORY + RUN_NAME + "_" + time_suffix + ".kraken.txt"
    freq_output = KRAKEN_FREQ_DIRECTORY + RUN_NAME + "_" + time_suffix + ".freq.txt"
    taxa_output = KRAKEN_TAXA_DIRECTORY + RUN_NAME + "_" + time_suffix + ".taxa.txt"
    krona_output = KRONA_DIRECTORY + RUN_NAME + "_" + time_suffix + ".krona.html"

    # Sort the new fasta files. We need to ensure the latest fasta file is not currently being written to.
    fasta_files.sort(key=lambda x: os.path.getmtime(x))

    # Use lsof | grep latest fasta file to see if the last file is currently being written to.
    # If so, remove it from the group.
    latest_fasta_file = fasta_files[len(fasta_files)-1]
    lsof_command = "lsof -w | grep %s | wc -l" % latest_fasta_file

    # Run the system command through the commands module so we can obtain the output of the command.
    lsof_status, lsof_output = commands.getstatusoutput(lsof_command)

    # If the latest fasta file is being written to we will remove it from the set of analysed fasta files.
    if int(lsof_output) != 0:
        print("Latest fasta file still being written to. Removing file from set of fasta files")
        fasta_files.remove(latest_fasta_file)
        if len(fasta_files) == 0:
            return list()

    for fasta_file in fasta_files:
        run_kraken(fasta_file, kraken_output)

        # Check to ensure kraken command completed appropriately?
        # If no reads return a match kraken will produce a blank file.
        lines = check_kraken_file(kraken_output)

        if lines == 0:
            print("Kraken completed but did not output anything.\n")
            print("Skipping rest of the pipeline.\n")
            return list()

        # Run the compute frequencies command
        summarise_kraken_output(kraken_output, freq_output)

        # Run taxa tree command
        create_taxa_tree(freq_output, taxa_output)

        # Run krona tools on the taxa files
        run_krona(krona_output)

    # Update and return to loop
    return fasta_files


def run_kraken(fasta_file, kraken_output):
    # Set kraken options
    kraken_options = []
    kraken_options.append("--threads %d" % THREAD_COUNT)
    kraken_options.append("--db %s" % KRAKEN_DATABASE)
    kraken_options.append("--only-classified-out")

    # Run kraken
    kraken_command = "kraken %s %s 1>> %s 2>> %s" % \
                     (' '.join(kraken_options), fasta_file, kraken_output, LOGFILE)
    os.system(kraken_command)


def run_krona(krona_output):
    # Create timestamp for inside the krona plot.
    running_m, running_s = divmod(time.time() - START_TIME, 60)
    running_h, running_m = divmod(running_m, 60)

    ktimportcommands = []
    ktimportcommands.append("-o %s" % krona_output)
    ktimportcommands.append("-n %s_%d:%02d:%02d" % (RUN_NAME, running_h, running_m, running_s))
    ktimportcommands.append("-c")

    for taxa_output in os.listdir(KRAKEN_TAXA_DIRECTORY):
        if taxa_output.endswith(".taxa.txt"):
            ktimportcommands.append(KRAKEN_TAXA_DIRECTORY + taxa_output)

    krona_command = "ktImportText %s" % ' '.join(ktimportcommands)
    logger = open(LOGFILE, 'a+')
    logger.write("Commencing Krona command.\n")
    logger.write("The command is: %s \n" % krona_command)

    os.system(krona_command)


def check_kraken_file(kraken_output):
    check_kraken_file_command = "cat %s | wc -l" % kraken_output
    check_kraken_file_status, check_kraken_file_output = commands.getstatusoutput(check_kraken_file_command)
    return int(check_kraken_file_output)


def summarise_kraken_output(kraken_output, freq_output):
    compute_frequencies_command = "summarise_kraken_output.R %s %s " % (kraken_output, freq_output)
    os.system(compute_frequencies_command)


def create_taxa_tree(freq_output, taxa_output):
    taxa_h = open(taxa_output, 'a+')
    with open(freq_output, "r") as f:
        # Convert tax_ids to lineage
        for line in f:
            line = line.rstrip()
            tax_id, freq = line.split("\t")
            try:
                lineage = ncbi.get_lineage(tax_id)
            except ValueError:
                print("Error: %s not found in database" % tax_id)
                continue
            names = ncbi.get_taxid_translator(lineage)
            lineage_names = [names[taxid] for taxid in lineage]
            taxa_h.write(freq + "\t" + "\t".join(lineage_names[1:]) + "\n")
    taxa_h.close()


def main():
    # Get arguments from the command line
    args = get_commandline_params()

    # Assign arguments from command line
    set_commandline_variables(args)

    # Set directories
    set_directories()

    start_log()

    # Run the kraken wrapper. Exits once no new fasta files have been created for x time
    kraken_wrapper()

    # Finish the log.
    end_log()

main()
