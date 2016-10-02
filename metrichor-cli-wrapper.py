#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import sys
import time

# This script is designed to exist as a wrapper for the metrichor-cli
# Ensure that you have metrichor-cli installed properly.
# Please refer to metrichor-cli-dependencies installation guide for further reference.
# If you have installed the metrichor-cli, ensure that you have sourced the metrichor-cli-setpaths.sh file.
# Also ensure you have created and sourced ~/.met_apikey
# Updates - removed the outputfolder option. It appears to be redundant.
# Conformed to functions.


# Declare global directories
WORKING_DIRECTORY = ""
READS_DIRECTORY = ""

# Declare global miscellaneous
version = 1.1
LOG_FILE = ""
START_TIME = ""
END_TIME = ""
RUN_NAME = ""
WORKFLOW = ""
WORKFLOW_CODES = {"2D_Basecalling": 1025, "WIMP_2D": 1042, "WIMP_1D": 1046, "2D_Basecalling_human_exome": 842}
DATE_PREFIX = str(time.strftime("%Y-%m-%d"))
PREMATURE_RUNTIME = 1000  # seconds, if metrichor breaks before 20 minutes is up, you've probably got an error!


# Configure arguments
def get_commandline_params():
    help_descriptor = "This is a wrapper script for parsing in a set of fast5 files to the metrichor cloud." + \
                    "This will create an uploaded and downloaded directory in the designated reads folder." + \
                    "A file names output.fastq will be created, containing all of the pass fastq reads."

    parser = argparse.ArgumentParser(description=help_descriptor)

    parser.add_argument('--version', action='version', version="%%(prog)s %s" % str(version))
    parser.add_argument("--run_name", nargs='?', dest="RUN_NAME", type=str,
                        help="This is the run name you wish to be present on all the files.",
                        required=True)
    parser.add_argument("--working_directory", nargs='?', dest="WORKING_DIRECTORY", type=str,
                        help="This is the directory that contains the reads folder.", required=True)
    parser.add_argument("--reads_directory", nargs='?', dest="READS_DIRECTORY", type=str,
                        help="This is the reads directory. If not specified, defaults to <working_directory>/reads")
    parser.add_argument("--workflow", nargs='?', dest="WORKFLOW_KEY", type=str, choices=WORKFLOW_CODES.keys(),
                        help="Which workflow would you like to run?", required=True)

    args = parser.parse_args()
    return args


def set_commandline_variables(args):
    global WORKING_DIRECTORY, READS_DIRECTORY
    global RUN_NAME, WORKFLOW

    RUN_NAME = args.RUN_NAME
    WORKING_DIRECTORY = args.WORKING_DIRECTORY
    WORKFLOW = WORKFLOW_CODES.get(args.WORKFLOW_KEY)
    READS_DIRECTORY = args.READS_DIRECTORY


def set_directories():
    global WORKING_DIRECTORY, READS_DIRECTORY
    global LOG_FILE
    # Check to ensure working directory exists.
    if not os.path.isdir(WORKING_DIRECTORY):
        error_message = "Error, working directory not a valid directory."
        sys.exit(error_message)
    WORKING_DIRECTORY = os.path.abspath(WORKING_DIRECTORY) + "/"

    # If reads directory not specified, presume within working directory.
    if READS_DIRECTORY:
        if not os.path.isdir(READS_DIRECTORY):
            error_message = "Error, reads folder does not exist."
            sys.exit(error_message)
        READS_DIRECTORY = os.path.abspath(READS_DIRECTORY) + "/"
    else:
        READS_DIRECTORY = WORKING_DIRECTORY + "reads/"

    # Create the log_file
    log_directory = WORKING_DIRECTORY + "log/"
    if not os.path.isdir(log_directory):
        os.mkdir(log_directory)
    LOG_FILE = log_directory + DATE_PREFIX + "_" + RUN_NAME + ".metrichor.log"

    # Change to working directory
    os.chdir(WORKING_DIRECTORY)


def start_log(metrichor_command):
    global START_TIME
    START_TIME = time.time()
    # Write to log file prior to running command\
    logger = open(LOG_FILE, 'a+')
    logger.write("Commencing Metrichor transfer at %s\n" % time.strftime("%c"))
    logger.write("The input into the wrapper script is %s\n" % sys.argv[:])
    logger.write("The command for running the metrichor-cli is: %s\n" % metrichor_command)
    logger.close()


def end_log():

    # Write to log file after running command
    logger = open(LOG_FILE, 'a+')
    logger.write("Completed Metrichor transfer at %s\n" % time.strftime("%c"))
    logger.write("Metrichor completed in %d\n" % (END_TIME - START_TIME))
    logger.close()


def error_log(metrichor_command):
    undefined_uploads_error_message = "TypeError: Cannot read property 'length' of undefined"
    memory_error_message = "HDF5-DIAG: Error detected in HDF5 (1.8.5-patch1) thread 0:"
    logger = open(LOG_FILE, 'a+')
    logger.write("It appears that the script finished early! %s\n" % time.strftime("%c"))
    logger.write("You may need to re run the command")
    debug_message = "This program can be buggy, you probably need to re run the command.\n" + \
                    "Because I'm a really nice programmer. I've saved it for you! " + \
                    "Only re-run the command if you see this error in your metrichor-cli log file:\n %s.\n \n" %\
                    undefined_uploads_error_message
    print(debug_message)
    print(metrichor_command)

    # This program is super buggy and I get another error, you now need to join the existing workflow.
    # Hence forth you need to rejoin an existing workflow.
    debug_message = "\n \n If you see this error in your log file:\n %s.\n" % memory_error_message + \
                    "If so will need to rejoin the workflow using the command printed below.\n" + \
                    "You can find the instance id from metrichor.com/user\n\n"
    print(debug_message)

    instructions = "metrichor-cli --join <insert instance_id_here> --inputfolder %s 2>> %s " % \
        (READS_DIRECTORY, LOG_FILE)

    print(instructions)


def run_metrichor():
    global END_TIME

    # Create metrichor command options
    metrichor_command_options = []
    metrichor_command_options.append("--apikey $MET_APIKEY")
    metrichor_command_options.append("--inputfolder %s" % READS_DIRECTORY)
    metrichor_command_options.append("--workflow %s" % WORKFLOW)
    metrichor_command_options.append("--fastq")
    metrichor_command_options.append("--qconcat")

    # Complete the metrichor command
    metrichor_command = "metrichor-cli %s 2>> %s" % (' '.join(metrichor_command_options), LOG_FILE)

    start_log(metrichor_command)

    # Run command
    os.system(metrichor_command)

    END_TIME = time.time()
    run_time = END_TIME - START_TIME
    if run_time < PREMATURE_RUNTIME:
        error_log(metrichor_command)
    else:
        end_log()


def main():
    # Obtain variables entered into commandline
    args = get_commandline_params()

    # Set these variables
    set_commandline_variables(args)

    # Set directories, check directories can be written to
    set_directories()

    # Run metrichor
    run_metrichor()

main()
