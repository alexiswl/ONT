#!/usr/bin/env python

import os
import time
import argparse
import sys
import commands
import h5py

# This script is designed to perform many of the functions used in poretools

# Set defaults
THREAD_COUNT_DEFAULT = 4  # number of cores when basecalling
WATCH_DEFAULT = 800  # number of seconds of no new reads before exiting
WORKING_DIRECTORY_DEFAULT = os.getcwd()
INVALID_SYMBOLS = "~`!@#$%^&*()-+={}[]:>;',</?*-+"

# Declare global directories
WORKING_DIRECTORY = ""
DOWNLOADS_DIRECTORY = ""
FASTQ_DIRECTORY = ""
PORETOOLS_DIRECTORY = ""
LOG_DIRECTORY = ""
FAIL_DIRECTORY = ""
FAIL_SUB_FOLDERS = {}
PASS_DIRECTORY = ""

# Declare global files
FASTQ_FILE = ""
LOG_FILE = ""
COMPLETION_FILE = ""

# Declare global miscellaneous
version = 1.1
RUN_NAME = ""
WATCH = 0
DATE_PREFIX = str(time.strftime("%Y-%m-%d"))
POST_SPLIT = False
IS_1D = False


def get_commandline_params():
    help_descriptor = "This is a comprehensive script which analyses files through the poretools." + \
                      "A fastq folder is created containing the 'best' read of each fast5 file." + \
                      "A poretools folder is created containing some run metrics."

    parser = argparse.ArgumentParser(description=help_descriptor)

    parser.add_argument('--version', action='version', version="%%(prog)s %s" % str(version))
    parser.add_argument("--run_name", nargs='?', dest="RUN_NAME", type=str,
                        help="This is the run name you wish to be present on all the files.",
                        required=True)
    parser.add_argument("--working_directory", nargs='?', dest="WORKING_DIRECTORY", type=str,
                        help="This is the main directory." +
                             "This directory is generally the parent directory of the reads folder." +
                             "If not specified, this is the current directory.")
    parser.add_argument("--downloads_directory", nargs='?', dest="DOWNLOADS_DIRECTORY", type=str,
                        help="This is the directory in which the reads will be placed in to." +
                             "If not specified, this will be <working_directory>/reads/downloads.")
    parser.add_argument("--fastq_file", nargs="?", dest="FASTQ_FILE", type=str,
                        help="This is the file you wish to parse your fastq file into. If not defined it will be:" +
                             "<working_directory>/<fastq>/<RUN_NAME>.fastq")
    parser.add_argument("--post_split", action='store_true', dest="POST_SPLIT",
                        help="Has metrichor finished and split your data in to pass and fail already?", default=False)
    parser.add_argument("--1D_run", action='store_true', dest="IS_1D", default=False,
                        help="Use this option if the run was 1D only.")
    parser.add_argument("--log_file", nargs="?", dest="LOG_FILE", type=str,
                        help="This is the logfile. If not defined it will be:" +
                             "<working_directory>/<log>/<DATE>_<RUN_NAME>.fastq")
    parser.add_argument("--watch", nargs='?', dest="WATCH", type=int,
                        help="How long are you willing to wait for metrichor to process a file before timing out?")
    args = parser.parse_args()
    return args


def set_commandline_variables(args):
    global WORKING_DIRECTORY, DOWNLOADS_DIRECTORY
    global RUN_NAME, FASTQ_FILE, LOG_FILE, WATCH, POST_SPLIT, IS_1D

    RUN_NAME = args.RUN_NAME
    WORKING_DIRECTORY = args.WORKING_DIRECTORY
    DOWNLOADS_DIRECTORY = args.DOWNLOADS_DIRECTORY
    FASTQ_FILE = args.FASTQ_FILE
    LOG_FILE = args.LOG_FILE
    WATCH = args.WATCH
    POST_SPLIT = args.POST_SPLIT
    IS_1D = args.IS_1D


def set_directories():
    global WORKING_DIRECTORY, DOWNLOADS_DIRECTORY, FASTQ_DIRECTORY, LOG_DIRECTORY, PORETOOLS_DIRECTORY
    global PASS_DIRECTORY, FAIL_DIRECTORY
    global FASTQ_FILE, LOG_FILE, WATCH, IS_1D

    if not WORKING_DIRECTORY:
        WORKING_DIRECTORY = WORKING_DIRECTORY_DEFAULT
    general_message = "Working directory not specified. Using current directory: %s. \n" % WORKING_DIRECTORY_DEFAULT
    print(general_message)

    # Checking to make sure that the working directory exists.
    if not os.path.isdir(WORKING_DIRECTORY):
        error_message = "Working directory does not exist. Please create or specify an existing directory."
        sys.exit(error_message)
    WORKING_DIRECTORY = os.path.realpath(WORKING_DIRECTORY) + "/"

    if DOWNLOADS_DIRECTORY:
        if not os.path.isdir(DOWNLOADS_DIRECTORY):
            error_message = "Reads directory does not exist. Please create or specify an existing directory."
            sys.exit(error_message)
    else:
        DOWNLOADS_DIRECTORY = WORKING_DIRECTORY + "reads/downloads/"
        if not os.path.isdir(DOWNLOADS_DIRECTORY):
            os.makedirs(DOWNLOADS_DIRECTORY)
        general_message = "Downloads directory has not been specified. Using %s \n" % DOWNLOADS_DIRECTORY
        print(general_message)

    FASTQ_DIRECTORY = WORKING_DIRECTORY + "fastq/"
    if not FASTQ_FILE:
        if not os.path.isdir(FASTQ_DIRECTORY):
            os.makedirs(FASTQ_DIRECTORY)
        FASTQ_FILE = FASTQ_DIRECTORY + DATE_PREFIX + "_" + RUN_NAME + ".fastq"
        general_message = "Fastq file has not been specified. Using %s \n" % FASTQ_FILE
        print(general_message)

    LOG_DIRECTORY = WORKING_DIRECTORY + "log/"
    if not LOG_FILE:
        if not os.path.isdir(LOG_DIRECTORY):
            os.mkdir(LOG_DIRECTORY)
        LOG_FILE = LOG_DIRECTORY + DATE_PREFIX + "_" + RUN_NAME + ".poretools.log"

    if not WATCH:
        WATCH = WATCH_DEFAULT
        general_message = "Watch parameter not specified, reverting to %d" % WATCH_DEFAULT
        print(general_message)

    PORETOOLS_DIRECTORY = WORKING_DIRECTORY + "poretools/"
    if not os.path.isdir(PORETOOLS_DIRECTORY):
        os.mkdir(PORETOOLS_DIRECTORY)

    PASS_DIRECTORY = DOWNLOADS_DIRECTORY + "pass/"
    FAIL_DIRECTORY = DOWNLOADS_DIRECTORY + "fail/"

    if not os.path.isdir(PASS_DIRECTORY):
        os.mkdir(PASS_DIRECTORY)
    if not os.path.isdir(FAIL_DIRECTORY):
        os.mkdir(FAIL_DIRECTORY)

    fail_sub_folders = ('Corrupted_files', 'No_template_data', 'Unknown_error', '1D_basecall_not_performed',
                        'Calibration_strand_detected')
    if IS_1D:
        fail_sub_folders = fail_sub_folders + ('1D_failed_quality_filters',)
    else:
        fail_sub_folders = fail_sub_folders + ('No_complement_data', '2D_basecall_not_performed',
                                               '2D_failed_quality_filters')

    for folder in fail_sub_folders:
        FAIL_SUB_FOLDERS[folder] = FAIL_DIRECTORY + folder + "/"
        if not os.path.isdir(FAIL_SUB_FOLDERS[folder]):
            os.mkdir(FAIL_SUB_FOLDERS[folder])


def check_valid_symbols(string):
    for s in string:
        if s in INVALID_SYMBOLS:
            error_message = "Error, invalid character in filename. Cannot have any of the following characters %s" \
                            % INVALID_SYMBOLS
            sys.exit(error_message)


def check_completion_file():
    global COMPLETION_FILE
    # In case we need to come back to running the file
    COMPLETION_FILE = PORETOOLS_DIRECTORY + DATE_PREFIX + "_" + RUN_NAME + ".completion.txt"
    if not os.path.isfile(COMPLETION_FILE):
        os.system("touch %s" % COMPLETION_FILE)
    old_fast5_files = []
    with open(COMPLETION_FILE, "r") as f:
        for line in f:
            line = line.rstrip()
            old_fast5_files.append(line)
    return old_fast5_files


def get_new_fast5_files():
    patience_counter = 0
    run_exhausted = False

    new_fast5_files = []
    while len(new_fast5_files) == 0:

        # Get new fast5 files list.
        new_fast5_files = [DOWNLOADS_DIRECTORY + fast5_file for fast5_file in os.listdir(DOWNLOADS_DIRECTORY)
                           if fast5_file.endswith(".fast5")]

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
    return new_fast5_files, run_exhausted


def still_writing(filename):
    lsof_command = "lsof | grep %s | wc -l" % filename
    lsof_status, lsof_output = commands.getstatusoutput(lsof_command)
    return int(lsof_output)


def run_poretools_fastq():
    old_fast5_files = check_completion_file()
    new_pass_files = [PASS_DIRECTORY + fast5_file for fast5_file in os.listdir(PASS_DIRECTORY)
                      if PASS_DIRECTORY + fast5_file not in old_fast5_files]

    # Run the set of poretools commands on the new fast5 files
    logger = open(LOG_FILE, 'a+')
    logger.write("Commencing poretools on %d files.\n" % len(new_pass_files))
    logger.close()
    for fast5_file in new_pass_files:
        extract_fastq_options = ["fastq"]
        extract_fastq_options.append("--type 2D")
        extract_fastq_command = "poretools %s %s 1>> %s 2>> %s" % \
                                (' '.join(extract_fastq_options), fast5_file, FASTQ_FILE, LOG_FILE)
        os.system(extract_fastq_command)
        old_fast5_files.append(fast5_file)
        completion_file_h = open(COMPLETION_FILE, 'a+')
        completion_file_h.write(fast5_file + "\n")
        completion_file_h.close()

    logger = open(LOG_FILE, 'a+')
    logger.write("Completed poretools on %d files.\n" % len(new_pass_files))
    logger.write("Commencing stats on %s" % PASS_DIRECTORY)
    logger.close()


def run_poretools_metrics():
    yield_reads_file = PORETOOLS_DIRECTORY + DATE_PREFIX + "_" + RUN_NAME + ".pass_reads.yield_plot.png"
    yield_bases_file = PORETOOLS_DIRECTORY + DATE_PREFIX + "_" + RUN_NAME + ".pass_bases.yield_plot.png"
    hist_file = PORETOOLS_DIRECTORY + DATE_PREFIX + "_" + RUN_NAME + ".hist_plot.png"
    stats_file = PORETOOLS_DIRECTORY + DATE_PREFIX + "_" + RUN_NAME + ".stats.txt"
    stats_file_tmp = PORETOOLS_DIRECTORY + DATE_PREFIX + "_" + RUN_NAME + ".stats.txt.tmp"

    yield_reads_command_options = ["yield_plot"]
    yield_reads_command_options.append("--saveas %s" % yield_reads_file)
    yield_reads_command_options.append("--plot-type %s" % "reads")
    yield_reads_command = "poretools %s %s 2>> %s" % (' '.join(yield_reads_command_options), PASS_DIRECTORY, LOG_FILE)

    yield_base_command_options = ["yield_plot"]
    yield_base_command_options.append("--saveas %s" % yield_bases_file)
    yield_base_command_options.append("--plot-type %s" % "basepairs")
    yield_base_command = "poretools %s %s 2>> %s" % (' '.join(yield_base_command_options), PASS_DIRECTORY, LOG_FILE)

    hist_command_options = ["hist"]
    hist_command_options.append("--saveas %s" % hist_file)
    hist_command = "poretools %s %s 2>> %s" % (' '.join(hist_command_options), PASS_DIRECTORY, LOG_FILE)

    os.system(yield_reads_command)
    os.system(yield_base_command)
    os.system(hist_command)

    # Export stats to stats file
    read_types = ("all", "fwd", "rev", "2D")
    for read_type in read_types:
        stats_command = "poretools stats --type %s %s 1>> %s 2>> %s" % \
                        (read_type, PASS_DIRECTORY, stats_file_tmp, LOG_FILE)
        stats_file_h = open(stats_file_tmp, "a+")
        stats_file_h.write(stats_command)
        stats_file_h.close()
        os.system(stats_command)
    os.system("mv %s %s" % (stats_file_tmp, stats_file))


def run_poretools_wrapper():
    # While loop initialisers
    run_exhausted = False
    while not run_exhausted:
        # Get new fast5 files
        new_fast5_files, run_exhausted = get_new_fast5_files()

        # Exit if no fast5 files found in specified time
        if run_exhausted:
            break

        # Sort new fast5 files
        new_fast5_files.sort(key=lambda x: os.path.getmtime(x))

        # Is latest file still being written to? Could be multiple files, generates recursive loop.
        while True:
            latest_fast5_file = new_fast5_files[len(new_fast5_files)-1]
            if not still_writing(latest_fast5_file):
                break
            print("Latest fast5 file still being written to. Removing file from set of fasta files")
            new_fast5_files.remove(latest_fast5_file)
            if len(new_fast5_files) == 0:
                break

        if len(new_fast5_files) == 0:
            time.sleep(60)
            continue
        # Move files by stats
        split_reads_by_attribute(new_fast5_files)

        run_poretools_fastq()
        run_poretools_metrics()

    print "No fast5 files downloaded from metrichor in the last %d seconds\n" % WATCH
    print "Exiting\n"


def split_reads_by_attribute(new_fast5_files):
    datasets = {}
    datasets['basecall_1D_summary_dataset'] = '/Analyses/Basecall_1D_000/Summary'
    datasets['event_detection_dataset'] = '/Analyses/EventDetection_000/Summary'
    datasets['calibration_summary_dataset'] = '/Analyses/Calibration_Strand_000/Summary'
    if IS_1D:
        datasets['segment_linear_dataset'] = '/Analyses/Segment_Linear_000/Summary'
    else:
        datasets['basecall_2D_summary_dataset'] = '/Analyses/Basecall_2D_000/Summary'
        datasets['hairpin_summary_dataset'] = '/Analyses/Hairpin_Split_000/Summary'

    for fast5_file in new_fast5_files:
        if not os.path.isfile(fast5_file):
            continue
        # Check to ensure that the file is not corrupt.
        try:
            f = h5py.File(fast5_file, 'r')
        except IOError:
            os.system("mv %s %s" % (fast5_file, FAIL_SUB_FOLDERS["Corrupted_files"]))
            continue
        # File not corrupt, move to folders accordingly.
        try:
            if IS_1D:
                if f[datasets['segment_linear_dataset']].attrs.values()[0] \
                        == "No template data found":
                    os.system("mv %s %s" % (fast5_file, FAIL_SUB_FOLDERS["No_template_data"]))
                elif f[datasets['basecall_1D_summary_dataset']].attrs.values()[0] \
                        == "1D basecall could not be performed":
                    os.system("mv %s %s" % (fast5_file, FAIL_SUB_FOLDERS["1D_basecall_not_performed"]))
                elif f[datasets['basecall_1D_summary_dataset']].attrs.values()[0] \
                        == "1D basecall failed quality filters":
                    os.system("mv %s %s" % (fast5_file, FAIL_SUB_FOLDERS["1D_failed_quality_filters"]))
                else:
                    # 1D Workflow was successful!
                    if not f[datasets['basecall_1D_summary_dataset']].attrs.values()[0] == "Workflow successful":
                        os.system("mv %s %s" % (fast5_file, FAIL_SUB_FOLDERS["Unknown_error"]))
                    else:
                        os.system("mv %s %s" % (fast5_file, PASS_DIRECTORY))
            else:
                if f[datasets['hairpin_summary_dataset']].attrs.values()[0] \
                        == "No template data found":
                    os.system("mv %s %s" % (fast5_file, FAIL_SUB_FOLDERS["No_template_data"]))
                elif f[datasets['basecall_1D_summary_dataset']].attrs.values()[0] \
                        == "No complement data found":
                    os.system("mv %s %s" % (fast5_file, FAIL_SUB_FOLDERS["No_complement_data"]))
                elif f[datasets['basecall_1D_summary_dataset']].attrs.values()[0] \
                        == "1D basecall could not be performed":
                    os.system("mv %s %s" % (fast5_file, FAIL_SUB_FOLDERS["1D_basecall_not_performed"]))
                elif f[datasets['basecall_2D_summary_dataset']].attrs.values()[0] \
                        == "2D basecall could not be performed":
                    os.system("mv %s %s" % (fast5_file, FAIL_SUB_FOLDERS["2D_basecall_not_performed"]))
                elif f[datasets['basecall_2D_summary_dataset']].attrs.values()[0] \
                        == "Exception thrown":
                    os.system("mv %s %s" % (fast5_file, FAIL_SUB_FOLDERS["Unknown_error"]))
                elif f[datasets['basecall_2D_summary_dataset']].attrs.values()[0] \
                        == "2D basecall failed quality filters":
                    os.system("mv %s %s" % (fast5_file, FAIL_SUB_FOLDERS["2D_failed_quality_filters"]))
                elif f[datasets['calibration_summary_dataset']].attrs.values()[0] \
                        == "Calibration strand detected":
                        os.system("mv %s %s" % (fast5_file, FAIL_SUB_FOLDERS["Calibration_strand_detected"]))
                else:
                    # 2D Workflow was successful!!
                    if f[datasets['basecall_2D_summary_dataset']].attrs.values()[0] != "Workflow successful":
                        print("Unknown error, moving %s to %s" % (fast5_file, FAIL_SUB_FOLDERS["Unknown_error"]))
                        os.system("mv %s %s" % (fast5_file, FAIL_SUB_FOLDERS["Unknown_error"]))
                    elif f[datasets['calibration_summary_dataset']].attrs.values()[0] != "Workflow successful":
                        print("Unknown error, moving %s to %s" % (fast5_file, FAIL_SUB_FOLDERS["Unknown_error"]))
                        os.system("mv %s %s" % (fast5_file, FAIL_SUB_FOLDERS["Unknown_error"]))
                    else:
                        os.system("mv %s %s" % (fast5_file, PASS_DIRECTORY))
        except IndexError:
            os.system("mv %s %s" % (fast5_file, FAIL_SUB_FOLDERS["Corrupted_files"]))
        except KeyError:
            os.system("mv %s %s" % (fast5_file, FAIL_SUB_FOLDERS["Corrupted_files"]))


def main():
    global RUN_NAME

    # Get commandline parameters
    args = get_commandline_params()

    # Set variables from command line
    set_commandline_variables(args)

    # Set the directories
    set_directories()

    # Check for invalid symbols in run_name
    check_valid_symbols(RUN_NAME)

    # Run poretools
    if not POST_SPLIT:
        run_poretools_wrapper()
    else:
        run_poretools_fastq()
        run_poretools_metrics()

main()
