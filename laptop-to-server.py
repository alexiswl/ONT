#!/usr/bin/env python
import os
import shutil
import time
import argparse
import sys

# This script is designed to transfer data from the output on the laptop produced by MinKNOW to a server.
# This script will be required to be run from a computer that has access to both the laptop and the server.
# Hence it is possible to run this script on the laptop concurrently with MinKNOW if it can see the server.

# Declare Global directories:
READS_DIRECTORY = ""
SERVER_DIRECTORY = ""
RUN_DIRECTORY = ""
DUMP_DIRECTORY = ""


# Declare Global Files
LOGFILE = ""

# Declare Global Miscellaneous
version = 1.1
RUN_NAME = ""
WATCH = 0
WATCH_DEFAULT = 800
INVALID_SYMBOLS = "~`!@#$%^&*()-+={}[]:>;',</?*-+"
DATE_SUFFIX = time.strftime("%Y-%m-%d-%H-%M-%S")
DATE_PREFIX = time.strftime("%Y_%m_%d")
START_TIME = time.time()

def get_commandline_params():
    help_descriptor = "This is a script designed to remove fast5 files from a laptop onto a server." + \
                      "There is not currently any support for FTP or for scp commands. This script only" + \
                      "works in circumstances where you can map the network drive. You only need three arguments" + \
                      "for this command to run. 1 - Run name, 2 - Reads directory, 3 - Server directory. The reads" + \
                      "will then placed into a folder YYYY_MM_DD_<RUN_NAME>/dump in the server directory."

    parser = argparse.ArgumentParser(description=help_descriptor)

    parser.add_argument('--version', action='version', version="%%(prog)s %s" % str(version))
    parser.add_argument("--run_name", nargs='?', dest="RUN_NAME", type=str,
                        help="This is a required argument. What is the name of your run as they appear on the fast5 " +
                             "files? User_Date_FlowcellID_MinIONID_sequencing_run_<RUNNAME>_5DigitBarcode_Channel_Read",
                        required=True)
    parser.add_argument("--reads_directory", nargs='?', dest="READS_DIRECTORY", type=str,
                        help="This is the directory that contains the fast5 files produced by MinKNOW.",
                        required="True")
    parser.add_argument("--server_directory", nargs='?', dest="SERVER_DIRECTORY", type=str,
                        help="This is the directory generally the parent directory of the run folder. If "
                             "the run folder + or its subdirectory <dump> folder do not exist, they will be created.",
                        required="True")
    parser.add_argument("--run_directory", nargs='?', dest="RUN_DIRECTORY", type=str,
                        help="This is the parent folder of the dump folder. If not specified, this will become" +
                             "<server_directory>/<run_directory>")
    parser.add_argument("--dump_directory", nargs='?', dest="DUMP_DIRECTORY", type=str,
                        help="This is the folder on the server that you would like to place the fast5 file in to." +
                             "If not specified, this becomes <run_directory>/dump")
    parser.add_argument("--watch", nargs='?', dest="WATCH", type=int,
                        help="This time (seconds) allowed with no new fast5 files" +
                             "entering the reads folder before exiting the script. Default set at 800")
    parser.add_argument("--logfile", nargs='?', dest="LOGFILE", type=str,
                        help="This is the file that some general notes are printed to. If not specified," +
                             "the file will be RUN_DIRECTORY/log/<run_name>.move.log")
    args = parser.parse_args()
    return args


def set_commandline_variables(args):
    global READS_DIRECTORY, SERVER_DIRECTORY, RUN_DIRECTORY, DUMP_DIRECTORY
    global RUN_NAME, WATCH, LOGFILE

    RUN_NAME = args.RUN_NAME
    READS_DIRECTORY = args.READS_DIRECTORY
    SERVER_DIRECTORY = args.SERVER_DIRECTORY
    RUN_DIRECTORY = args.RUN_DIRECTORY
    DUMP_DIRECTORY = args.DUMP_DIRECTORY

    WATCH = args.WATCH
    LOGFILE = args.LOGFILE


def check_valid_symbols(string):
    for s in string:
        if s in INVALID_SYMBOLS:
            error_message = "Error, invalid character in filename. Cannot have any of the following characters %s" \
                            % INVALID_SYMBOLS
            sys.exit(error_message)


def set_directories():
    global READS_DIRECTORY, RUN_DIRECTORY, SERVER_DIRECTORY
    global WATCH, LOGFILE, DUMP_DIRECTORY
    # Checking to ensure that the reads directory exists
    if not os.path.isdir(READS_DIRECTORY):
        error_message = "Error: cannot locate or find reads directory %s" % READS_DIRECTORY
        sys.exit(error_message)
    READS_DIRECTORY = os.path.abspath(READS_DIRECTORY) + "/"

    if not os.path.isdir(SERVER_DIRECTORY):
        error_message = "Error: cannot locate or find server directory %s" % SERVER_DIRECTORY
        sys.exit(error_message)
    SERVER_DIRECTORY = os.path.abspath(SERVER_DIRECTORY) + "/"

    # Checking to ensure that the run directory exists.
    if RUN_DIRECTORY:
        if not os.path.isdir(RUN_DIRECTORY):
            error_message = "Error: run directory specified but does not exist %s" % RUN_DIRECTORY
            sys.exit(error_message)
    else:
        RUN_DIRECTORY = SERVER_DIRECTORY + DATE_PREFIX + "_" + RUN_NAME + "/"
        general_message = "Run directory not specified. Using %s" % RUN_DIRECTORY
        print(general_message)
        if not os.path.isdir(RUN_DIRECTORY):
            os.mkdir(RUN_DIRECTORY)
            os.mkdir(RUN_DIRECTORY)
    RUN_DIRECTORY = os.path.abspath(RUN_DIRECTORY) + "/"

    # Checking to ensure that the dump directory exists.
    if DUMP_DIRECTORY:
        if not os.path.isdir(DUMP_DIRECTORY):
            error_message = "Error: dump directory specified but does not exist %s" % DUMP_DIRECTORY
            sys.exit(error_message)
    else:
        DUMP_DIRECTORY = RUN_DIRECTORY + "dump/"
        general_message = "Dump directory not defined. Using %s" % DUMP_DIRECTORY
        print(general_message)
        if not os.path.isdir(DUMP_DIRECTORY):
            os.mkdir(DUMP_DIRECTORY)
    DUMP_DIRECTORY = os.path.abspath(DUMP_DIRECTORY) + "/"

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
        LOGFILE = log_directory + DATE_PREFIX + "_" + RUN_NAME + ".transfer.log"
        general_message = "Log file not defined, using %s" % LOGFILE
        print(general_message)


def start_log():
    logger = open(LOGFILE, 'a+')
    logger.write("The time is %s:\n" % time.strftime("%c"))
    logger.write("Commencing transfer of reads from %s to %s" % (READS_DIRECTORY, DUMP_DIRECTORY))
    logger.close()
    return time.time()


def end_log(run_exhausted, files_moved):
    end_time = time.time()
    logger = open(LOGFILE, 'a+')
    logger.write("No fast5 files found for %d seconds\n" % WATCH)
    logger.write("Moved %d files\n" % files_moved)
    logger.write("Process completed in %d seconds.\n" % (end_time - START_TIME))
    if not run_exhausted:
        logger.write("Process exited not due to timeout. Check for errors.")
    logger.write("Exiting\n")


def free_modifications():
    for root, dirs, files in os.walk(RUN_DIRECTORY):
        for d in dirs:
            os.chmod(os.path.join(root, d), 777)
        for f in files:
            os.chmod(os.path.join(root, f), 777)


def commence_transfer():
    # We now begin the process of moving reads across from the read_directory to the server directory
    # to prevent the computer from filling up.
    # We want to be careful to ensure that reads do not get moved across twice
    # and that only fast5 files are moved across.
    run_exhausted = False
    files_moved = 0
    patience_counter = 0

    os.chdir(READS_DIRECTORY)
    free_modifications()

    while not run_exhausted:
        fast5_files = []
        while len(fast5_files) == 0:
            # Create an array of all the fast5 files in the directory the MinION is writing to.
            fast5_files = [fast5 for fast5 in os.listdir(READS_DIRECTORY)
                           if fast5.endswith('.fast5') and RUN_NAME in fast5]

            # Important to transfer the oldest files first.
            fast5_files.sort(key=lambda x: os.path.getmtime(x))

            # Did we pick anything up?
            if len(fast5_files) != 0:
                break

            # Didn't pick anything up...
            # Have we exceeded the number of mini-sleeps?
            if patience_counter > WATCH:
                run_exhausted = True
                return run_exhausted, files_moved

            # No? Take a minute sleep.
            if patience_counter != 0:
                abstinence_message = "No fast5 files found in the last %d seconds.\n" % patience_counter
                sleeping_message = "Waiting 60 seconds, breaking in %d if no more reads created.\n" \
                                   % (WATCH - patience_counter)
                logger = open(LOGFILE, 'a+')
                print(abstinence_message)
                print(sleeping_message)
                logger.write(abstinence_message + "\n")
                logger.write(sleeping_message + "\n")

            time.sleep(60)
            patience_counter += 60

        # Out of the while loop, either fast5 files have been found or run is exhausted.
        patience_counter = 0  # Must be consecutive minute sleeps to exhaust the run.

        # Move the files from the MinION directory to the server directory
        for read in fast5_files:
            if not os.path.isfile(DUMP_DIRECTORY + read):
                shutil.move(READS_DIRECTORY + read, DUMP_DIRECTORY)
                files_moved += 1
            else:
                print "Warning, %s already exists in dump directory. Deleting from laptop." % read
                os.remove(READS_DIRECTORY + read)


def main():
    # Get command line params
    args = get_commandline_params()

    # Set variables from command line
    set_commandline_variables(args)

    # Set configure directories
    set_directories()

    # Check for invalid symbols in RUN_NAME
    check_valid_symbols(RUN_NAME)

    # Write to log commencing transfer:
    start_log()

    # Run transfer
    run_exhausted, files_moved = commence_transfer()

    # Run has been exhausted, write to log
    end_log(run_exhausted, files_moved)

main()
