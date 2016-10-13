#!/usr/bin/env python
import os
import time
import shutil
import argparse
import sys

# This script is designed to copy fast5 files from the 'dump' folder.
# Perform a rapid 1D analysis on the files using nanonet and then place them in the reads folder.
# The reads folder can be seen by metrichor for more accurate basecalling.

# Set defaults
THREAD_COUNT_DEFAULT = 4  # number of cores when basecalling
WATCH_DEFAULT = 800  # number of seconds of no new reads before exiting
WORKING_DIRECTORY_DEFAULT = os.getcwd()
INVALID_SYMBOLS = "~`!@#$%^&*()-+={}[]:>;',</?*-+"

# Declare global directories
WORKING_DIRECTORY = ""
DUMP_DIRECTORY = ""
READS_DIRECTORY = ""
FASTA_DIRECTORY = ""
DOWNLOADS_DIRECTORY = ""
FASTA_2D_SUBDIRECTORIES = {}

# Declare global miscellaneous
version = 1.1
THREAD_COUNT = 0
WATCH = 0
RUN_NAME = ""
DATE_PREFIX = str(time.strftime("%Y-%m-%d"))
LOG_FILE = ""
READS_PER_FASTA = 100
START_TIME = time.time()
IS_1D = False


def get_commandline_params():
    help_descriptor = "This is a comprehensive script which copies files from the dump folder." + \
                      "These are then placed in a temporary directory and read by nanonet which produces a " + \
                      "1D fasta file of the fast5 files in the directory." + \
                      "Once complete, these files are moved to the reads directory."

    parser = argparse.ArgumentParser(description=help_descriptor)

    parser.add_argument('--version', action='version', version="%%(prog)s %s" % str(version))
    parser.add_argument("--run_name", nargs='?', dest="RUN_NAME", type=str,
                        help="This is the run name you wish to be present on all the fasta files.",
                        required=True)
    parser.add_argument("--working_directory", nargs='?', dest="WORKING_DIRECTORY", type=str,
                        help="This is the main directory." +
                             "This directory is generally the parent directory of the dump folder." +
                             "If not specified, this is the current directory.")
    parser.add_argument("--basecalling_type", nargs='?', dest="IS_1D", choices=('1D', '2D'),
                        help="Which basecalling type would you like to use?")
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
    parser.add_argument("--log_file", nargs='?', dest="LOG_FILE", type=str,
                        help="Enter where you would like to append the log. " +
                             "Default will be log/DATE_RUNNAME.nanonet.log")
    args = parser.parse_args()
    return args


def set_commandline_variables(args):
    global WORKING_DIRECTORY, DOWNLOADS_DIRECTORY, DUMP_DIRECTORY, READS_DIRECTORY, FASTA_DIRECTORY
    global RUN_NAME, WATCH, THREAD_COUNT, LOG_FILE, IS_1D
    RUN_NAME = args.RUN_NAME
    WORKING_DIRECTORY = args.WORKING_DIRECTORY
    DUMP_DIRECTORY = args.DUMP_DIRECTORY
    READS_DIRECTORY = args.READS_DIRECTORY
    FASTA_DIRECTORY = args.FASTA_DIRECTORY
    THREAD_COUNT = args.THREAD_COUNT
    WATCH = args.WATCH
    LOG_FILE = args.LOG_FILE
    if args.IS_1D == "1D":
        IS_1D = True


def get_time():
    return str(time.strftime("%Y-%m-%d-%H-%M-%S"))


def check_valid_symbols(string):
    # Ensure sample name does not contain any invalid symbols
    for s in string:
        if s in INVALID_SYMBOLS:
            error_message = "Error, invalid character in %s. Cannot have any of the following characters %s" \
                            % (string, INVALID_SYMBOLS)
            sys.exit(error_message)


def set_directories():
    global WORKING_DIRECTORY, DUMP_DIRECTORY, READS_DIRECTORY, FASTA_DIRECTORY
    global LOG_FILE, THREAD_COUNT, WATCH
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
    DUMP_DIRECTORY = os.path.realpath(DUMP_DIRECTORY) + "/"

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
    READS_DIRECTORY = os.path.realpath(READS_DIRECTORY) + "/"

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

    FASTA_DIRECTORY = os.path.abspath(FASTA_DIRECTORY) + "/"

    if not IS_1D:
        set_2d_subdirectories()

    if not THREAD_COUNT:
        THREAD_COUNT = THREAD_COUNT_DEFAULT
        general_message = "Thread count has not been specified. Using %s \n" % THREAD_COUNT_DEFAULT
        print(general_message)

    if not WATCH:
        WATCH = WATCH_DEFAULT
        general_message = "Watch has not been specified. Using %s \n" % WATCH_DEFAULT
        print(general_message)

    if LOG_FILE:
        if not os.path.isfile(LOG_FILE):
            error_message = "Error, log file defined but does not exist."
            sys.exit(error_message)
    else:
        log_directory = WORKING_DIRECTORY + "log/"
        if not os.path.isdir(log_directory):
            os.mkdir(log_directory)
        LOG_FILE = log_directory + DATE_PREFIX + "_" + RUN_NAME + ".nanonet.log"


def set_2d_subdirectories():
    global FASTA_2D_SUBDIRECTORIES
    FASTA_2D_SUBDIRECTORIES = {"2D": FASTA_DIRECTORY + "2D/", "Template": FASTA_DIRECTORY + "Template/",
                               "Complement": FASTA_DIRECTORY + "Complement/"}

    for folder in FASTA_2D_SUBDIRECTORIES:
        if not os.path.isdir(FASTA_DIRECTORY + folder):
            os.mkdir(FASTA_DIRECTORY + folder)


def initialise_dictionary():
    # Initialise the directory dictionary: keeps track of files in much less time
    channel_numbers = range(1, 513)
    channel_list = []

    for number in channel_numbers:
        channel_list.append("ch" + str(number))
    d = {channel: 0 for channel in channel_list}

    # Need to check for files in the read directory: Say if this script needs to be restarted
    # Dictionary updated or left at zero if nothing in the reads directory
    fast5_files = [READS_DIRECTORY + fast5_file for fast5_file in os.listdir(READS_DIRECTORY)
                   if fast5_file.endswith('.fast5')]
    for fast5_file in fast5_files:
        if not (os.path.isfile(fast5_file) and fast5_file.endswith('.fast5')):
            print fast5_file
            continue  # downloads or uploads folder
        channel = fast5_file.split('_')[-3]
        read = fast5_file.split('_')[-2]
        read_number = int(read.replace("read", ''))
        if channel == "ch325":
            print read, read_number, d[channel]
        if read_number > d[channel]:
            if channel == "ch325":
                print read, read_number, d[channel], "change"
            d[channel] = read_number

    # Metrichor may have taken some of these reads too!
    uploaded_directory = READS_DIRECTORY + "uploaded/"
    fast5_files = [uploaded_directory + fast5_file for fast5_file in os.listdir(uploaded_directory)
                   if fast5_file.endswith('.fast5')]
    if os.path.isdir(uploaded_directory):
        for fast5_file in fast5_files:
            if not (os.path.isfile(fast5_file) and fast5_file.endswith('.fast5')):
                print fast5_file
                continue
            channel = fast5_file.split('_')[-3]
            read = fast5_file.split('_')[-2]
            read_number = int(read.replace("read", ''))
            if channel == "ch325":
                print read, read_number, d[channel]
            if read_number > d[channel]:
                if channel == "ch325":
                    print read, read_number, d[channel], "change_up"
                d[channel] = read_number

    return d.copy()


def run_nanonet_wrapper():
    # While loop initialisers
    run_exhausted = False
    d = initialise_dictionary()
    update_d = d.copy()
    print(d)

    logger = open(LOG_FILE, 'a+')
    logger.write("Completed initialising dictionary. Commencing nanonet.\n")
    logger.close()

    while not run_exhausted:
        new_fast5_files = []
        patience_counter = 0
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
        if not run_exhausted:
            run_nanonet(new_fast5_files)
    print "No fast5 files dumped to server in the last %d seconds\n" % WATCH
    print "Exiting\n"


def run_nanonet(fast5_files):
    # Create a tmp_directory to call fast5 files in
    two_d_prefix = "%s%s_%s" % (FASTA_DIRECTORY, RUN_NAME, get_time())
    one_d_prefix = "%s%s_1D_%s" % (FASTA_DIRECTORY, RUN_NAME, get_time())

    # Run nanonet command on tmp_nanonet_directory
    tmp_nanonet_directory = "%s%s/" % (READS_DIRECTORY, get_time())
    os.mkdir(tmp_nanonet_directory)

    # Move reads to main reads directory for metrichor to read
    for index, read in enumerate(fast5_files):
        shutil.copy2(DUMP_DIRECTORY + read, tmp_nanonet_directory)
        if (index+1) % READS_PER_FASTA == 0:
            if IS_1D:
                nanonet_command = "nanonetcall --jobs %d %s %s.fasta 2>> %s" % \
                              (THREAD_COUNT, tmp_nanonet_directory, one_d_prefix, LOG_FILE)
            else:
                nanonet_command = "nanonet2d --jobs %d %s %s 2>> %s" % \
                                  (THREAD_COUNT, tmp_nanonet_directory, two_d_prefix, LOG_FILE)
            os.system(nanonet_command)
            # Now move the files to the reads folder and create another tmp directory
            # if there are any files left.
            for fast5_file in os.listdir(tmp_nanonet_directory):
                shutil.move(tmp_nanonet_directory + fast5_file, READS_DIRECTORY)
            os.rmdir(tmp_nanonet_directory)
            tmp_nanonet_directory = "%s%s/" % (READS_DIRECTORY, get_time())
            two_d_prefix = "%s%s_%s" % (FASTA_DIRECTORY, RUN_NAME, get_time())
            one_d_prefix = "%s%s_1D_%s" % (FASTA_DIRECTORY, RUN_NAME, get_time())
            if index != len(fast5_files) - 1:
                os.mkdir(tmp_nanonet_directory)

    # Run nanonet command on remainder of files:
    if os.path.isdir(tmp_nanonet_directory):
        if IS_1D:
            nanonet_command = "nanonetcall --jobs %d %s %s.fasta 2>> %s" % \
                          (THREAD_COUNT, tmp_nanonet_directory, one_d_prefix, LOG_FILE)
        else:
            nanonet_command = "nanonet2d --jobs %d %s %s 2>> %s" % \
                              (THREAD_COUNT, tmp_nanonet_directory, two_d_prefix, LOG_FILE)
        os.system(nanonet_command)
        # Move the files to the reads folder.
        for fast5_file in os.listdir(tmp_nanonet_directory):
            shutil.move(tmp_nanonet_directory + fast5_file, READS_DIRECTORY)
        os.rmdir(tmp_nanonet_directory)
    if not IS_1D:
        split_fasta_by_type()


def split_fasta_by_type():
    for fastafile in os.listdir(FASTA_DIRECTORY):
        if fastafile.endswith("2D.fasta"):
            shutil.move(FASTA_DIRECTORY + fastafile, FASTA_2D_SUBDIRECTORIES['2D'])
        elif fastafile.endswith("tmp.fasta"):
            shutil.move(FASTA_DIRECTORY + fastafile, FASTA_2D_SUBDIRECTORIES['Template'])
        else:
            shutil.move(FASTA_DIRECTORY + fastafile, FASTA_2D_SUBDIRECTORIES['Complement'])


def start_log():
    logger = open(LOG_FILE, 'a+')
    logger.write("Commencing nanonet wrapper at %s\n" % time.strftime("%c"))


def end_log():
    end_time = time.time()
    logger = open(LOG_FILE, 'a+')
    logger.write("Complete nanonet wrapper at %s\n" % time.strftime("%c"))
    logger.write("Total running time %s" % str(end_time - START_TIME))


def main():
    # Get command line arguments
    args = get_commandline_params()

    # Set command line variables and create directories
    set_commandline_variables(args)
    set_directories()

    # Check no invalid symbols in the run name
    check_valid_symbols(RUN_NAME)

    # Initial write to log
    start_log()

    # Run nanonet
    run_nanonet_wrapper()

    # Run finished or timed out. Finish log
    end_log()

main()
