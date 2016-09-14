#!/usr/bin/env python
import os
import time
import shutil
import argparse
import sys

# This script is designed to copy fast5 files from the 'dump' folder.
# Perform a rapid 1D analysis on the files using nanonet and then place them in the reads folder.
# The reads folder can be seen by metrichor for more accurate basecalling.

# Configure arguments
help_descriptor = "This is a comprehensive script which copies files from the dump folder." + \
                  "These are then placed in a temporary directory and read by nanonet which produces a " + \
                  "1D fasta file of the fast5 files in the directory." + \
                  "Once complete, these files are moved to the reads directory."

parser = argparse.ArgumentParser(description=help_descriptor)

parser.add_argument('--version', action='version', version="%(prog)s 1.0")
parser.add_argument("--run_name", nargs='?', dest="RUN_NAME", type=str,
                    help="This is the run name you wish to be present on all the fasta files.",
                    required=True)
parser.add_argument("--working_directory", nargs='?', dest="WORKING_DIRECTORY", type=str,
                    help="This is the main directory." +
                         "This directory is generally the parent directory of the dump folder." +
                         "If not specified, this is the current directory.")
parser.add_argument("--dump_directory", nargs='?', dest="DUMP_DIRECTORY", type=str,
                    help="This is the directory which fast5 files are being placed in to." +
                         "If not specified, this will <working_directory>/dump")

parser.add_argument("--reads_directory", nargs='?', dest="READS_DIRECTORY", type=str,
                    help="This is the directory in which the reads will be placed in to." +
                         "If not specified, will be a created within the working directory.")
parser.add_argument("--fasta_directory", nargs="?", dest="FASTA_DIRECTORY", type=str,
                    help="This is the directory in which fasta files will be placed in to." +
                         "If not specified, will be created within the working directory.")
parser.add_argument("--threads", nargs='?', dest="THREAD_COUNT", type=int,
                    help="Number of processors used during nanonet command. Defaults to 4.")

parser.add_argument("--watch", nargs='?', dest="WATCH", type=int,
                    help="The time (seconds) allowed with no new fast5 files" +
                         "entering the dump directory before exiting the script. Default set at 800")
args = parser.parse_args()

# Assign inputs
RUN_NAME = args.RUN_NAME
WORKING_DIRECTORY = args.WORKING_DIRECTORY
DUMP_DIRECTORY = args.DUMP_DIRECTORY
READS_DIRECTORY = args.READS_DIRECTORY
FASTA_DIRECTORY = args.FASTA_DIRECTORY
THREAD_COUNT = args.THREAD_COUNT
WATCH = args.WATCH

# Defaults
THREAD_COUNT_DEFAULT = 4  # number of cores when basecalling
WATCH_DEFAULT = 800  # number of seconds of no new reads before exiting
WORKING_DIRECTORY_DEFAULT = os.getcwd()
INVALID_SYMBOLS = "~`!@#$%^&*()-+={}[]:>;',</?*-+"

# Set the time
initial_date_suffix = time.strftime("%Y-%m-%d-%H-%M-%S")

# Ensure sample name does not contain any invalid symbols
for s in RUN_NAME:
    if s in INVALID_SYMBOLS:
        error_message = "Error, invalid character in filename. Cannot have any of the following characters %s" \
                        % INVALID_SYMBOLS
        sys.exit(error_message)

# Checking to see if working directory has been defined
if not WORKING_DIRECTORY:
    WORKING_DIRECTORY = WORKING_DIRECTORY_DEFAULT
    general_message = "Working directory not specified. Using current directory: %s. \n" % WORKING_DIRECTORY_DEFAULT
    print(general_message)

# Checking to make sure that the working directory exists.
if not os.path.isdir(WORKING_DIRECTORY):
    error_message = "Working directory does not exist. Please create or specify an existing directory."
    sys.exit(error_message)
WORKING_DIRECTORY = os.path.realpath(WORKING_DIRECTORY) + "/"

# Ensuring that other directories exist or assigning to defaults.
if DUMP_DIRECTORY:
    if not os.path.isdir(DUMP_DIRECTORY):
        error_message = "Dump directory does not exist. Please create or specify an existing directory."
        sys.exit(error_message)
else:
    DUMP_DIRECTORY = WORKING_DIRECTORY + "dump/"
    if not os.path.isdir(DUMP_DIRECTORY):
        error_message = "Dump directory does not exist. Please create or specify an existing directory."
        sys.exit(error_message)
    general_message = "Dump directory has not been specified. Using %s \n" % DUMP_DIRECTORY
    print(general_message)

if READS_DIRECTORY:
    if not os.path.isdir(READS_DIRECTORY):
        error_message = "Reads directory does not exist. Please create or specify an existing directory."
        sys.exit(error_message)
else:
    READS_DIRECTORY = WORKING_DIRECTORY + "reads/"
    if not os.path.isdir(READS_DIRECTORY):
        os.makedirs(READS_DIRECTORY)
    general_message = "Reads directory has not been specified. Using %s \n" % READS_DIRECTORY
    print(general_message)

if FASTA_DIRECTORY:
    if not os.path.isdir(FASTA_DIRECTORY):
        error_message = "Fasta directory does not exist. Please create or specify an existing directory."
        sys.exit(error_message)
else:
    FASTA_DIRECTORY = WORKING_DIRECTORY + "fasta/"
    if not os.path.isdir(FASTA_DIRECTORY):
        os.makedirs(FASTA_DIRECTORY)
    general_message = "Fasta directory has not been specified. Using %s \n" % FASTA_DIRECTORY
    print(general_message)

if not THREAD_COUNT:
    THREAD_COUNT = THREAD_COUNT_DEFAULT
    general_message = "Thread count has not been specified. Using %s \n" % THREAD_COUNT_DEFAULT
    print(general_message)

if not WATCH:
    WATCH = WATCH_DEFAULT
    general_message = "Watch has not been specified. Using %s \n" % WATCH_DEFAULT
    print(general_message)

# Initialise the directory dictionary: keeps track of files in much less time
channel_numbers = range(1, 513)
channel_list = []

for number in channel_numbers:
    channel_list.append("ch" + str(number))

d = {channel: 0 for channel in channel_list}

# Need to check for files in the read directory: Say if this script needs to be restarted
# Dictionary updated or left at zero if nothing in the reads directory

for fast5_file in os.listdir(READS_DIRECTORY):
    channel = fast5_file.split('_')[-3]
    read = fast5_file.split('_')[-2]
    read_number = int(read.replace("read", ''))
    if read_number > d[channel]:
        d[channel] = read_number

update_d = d.copy()
# While loop initialisers
new_fast5_files = []
run_exhausted = False
patience_counter = 0

while not run_exhausted:
    while len(new_fast5_files) == 0:

        # Get new fast5 files list.
        for fast5_file in os.listdir(DUMP_DIRECTORY):
            channel = fast5_file.split('_')[-3]
            read = fast5_file.split('_')[-2]
            read_number = int(read.replace("read", ''))
            if d[channel] < read_number:
                new_fast5_files.append(fast5_file)
                if update_d[channel] < read_number:
                    update_d[channel] = read_number
        d = update_d.copy()
        # Break if one or more fast5 files were found
        if len(new_fast5_files) != 0:
            break

        # Didn't pick anything up...
        # Have we exceeded the number of mini-sleeps?
        if patience_counter > WATCH:
            run_exhausted = True
            break

        # No? Take a minute sleep.
        if patience_counter != 0:
            print "No fast5 files found in the last %d seconds.\n" % patience_counter
            print "Waiting 60 seconds, breaking in %d if no more reads created.\n" % (WATCH - patience_counter)
        time.sleep(60)
        patience_counter += 60

    # Out of while loop, fast5 files found or run is exhausted.
    patience_counter = 0  # must be consistent absence of reads

    # Create a tmp_directory to call fast5 files in
    time_of_command = round(time.time())
    tmp_nanonet_directory = "%s/%d" % (READS_DIRECTORY, time_of_command)
    os.makedirs(tmp_nanonet_directory)  # there shouldn't be any need to check...

    fasta_file = "%s/%s_1D_%d.fasta" % (FASTA_DIRECTORY, RUN_NAME, time_of_command)
    for read in new_fast5_files:
        shutil.copy2(DUMP_DIRECTORY + "/" + read, tmp_nanonet_directory)

        # Run nanonet command on tmp_nanonet_directory
    nanonet_command = "nanonetcall --jobs %d %s > %s" % (THREAD_COUNT, tmp_nanonet_directory, fasta_file)
    os.system(nanonet_command)

    # Move reads to main reads directory for metrichor to read
    for read in os.listdir(tmp_nanonet_directory):
        shutil.move(tmp_nanonet_directory + "/" + read, READS_DIRECTORY)

        # Remove nanonet directory
    os.rmdir(tmp_nanonet_directory)

    # reset while loop parameters
    new_fast5_files = []

print "No fast5 files dumped to server in the last %d seconds\n" % WATCH
print "Exiting\n"
