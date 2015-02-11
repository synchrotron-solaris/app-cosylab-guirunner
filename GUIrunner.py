__author__ = 'Cosylab'

import sys
import os
import argparse
import subprocess

GIT_BRANCH = "production"
CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
# Static configuration
GIT_REPOSITORY_CSV = ["git://git.m.cps.uj.edu.pl/facilityconfiguration/conf-cosylab-synchrotroncsv.git", "git://git.m.cps.uj.edu.pl/facilityconfiguration/conf-cosylab-bl05idcsv.git", "git://git.m.cps.uj.edu.pl/facilityconfiguration/conf-cosylab-bl04bmcsv.git"]
DEFAULT_CSV_FOLDER = [CURRENT_PATH + "/Synchrotron_CSV", CURRENT_PATH + "/UarpesBL_CSV", CURRENT_PATH + "/PeemBL_CSV"]
GIT_REPOSITORY_GUI = ["git://git.m.cps.uj.edu.pl/controlroomsoftware/app-cosylab-synchrotronguis.git", "git://git.m.cps.uj.edu.pl/controlroomsoftware/app-cosylab-bl05idguis.git", "git://git.m.cps.uj.edu.pl/controlroomsoftware/app-cosylab-bl04bmguis.git"]
DEFAULT_GUI_FOLDER = [CURRENT_PATH + "/Synchrotron_GUIs", CURRENT_PATH + "/UarpesBL_GUIs", CURRENT_PATH + "/PeemBL_GUIs"]

GIT_REPOSITORY_VIEW = "git://git.m.cps.uj.edu.pl/controlroomsoftware/app-cosylab-controlprogram.git"
DEFAULT_VIEW_FOLDER = CURRENT_PATH + "/ControlProgram"
OVERVIEW_GUI_NAME = "ControlProgram.py"

CSV_FILE_NAME = ["synchrotron_devices.csv", "BL-05ID.csv", "BL-04BM.csv"]
VIEW_SELECTION = ["Synchrotron", "Uarpes", "Peem"]
TITLES = ["\"Solaris Synchrotron Control Program\"", "\"Uarpes Beamline Control Program\"", "\"Peem Beamline Control Program\""]

# Error messages
NO_GIT_CHECK_MSG = "Not checking for updates. Your files might be old or corrupted."
WRONG_VIEW = "\033[91mDesired view does not exist.\033[0m\nPossible views are: " + str(VIEW_SELECTION).lstrip("[").rstrip("]")
ERROR_UPDATE = "\033[91mErrors occurred during updating. Please fix them and start the runner again.\033[0m"
ERROR_RUN_CP = "\033[91mErrors occurred when trying to run the Control Program. Please fix them and start the runner again.\033[0m"
UNBALANCED_FOLDERS_LINKS = "Number of links and folders doesn't match."


def main():

    # Parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--noCheck', action='store_true', help="Don't check GIT repo for updates.")
    parser.add_argument('--noStart', action='store_true', help="Don't start the control program, unly check GIT repo for updates.")
    parser.add_argument('--view', action='store', type=str, default=VIEW_SELECTION[0], help="Select system to overview.")
    parser.add_argument('--repoCSV', action='store', type=str, help="Use custom repository link for cvs file.")
    parser.add_argument('--localCSV', action='store', type=str, help="Use custom folder for csv file.")
    parser.add_argument('--repoGUI', action='store', type=str, help="Use custom repository link for GUI files.")
    parser.add_argument('--localGUI', action='store', type=str,  help="Use custom folder for GUI files.")
    parser.add_argument('--repoCP', action='store', type=str, default=GIT_REPOSITORY_VIEW, help="Use custom repository link for GUI files.")
    parser.add_argument('--localCP', action='store', type=str, default=DEFAULT_VIEW_FOLDER, help="Use custom folder for VIEW files.")
    parser.add_argument('-v', dest="verbose", help='Verbose - log files for custom GUIs to user home folder.', action="store_true")
    args = parser.parse_args()


    # Return status code will be 0 if everything is OK
    status_code = 0

    # Fill info if user did not provide
    try:
        # Get desired view
        a = VIEW_SELECTION.index(args.view)

        # Check if CSV needs updating
        if args.repoCSV is None:
            args.repoCSV = GIT_REPOSITORY_CSV[a]
        if args.localCSV is None:
            args.localCSV = DEFAULT_CSV_FOLDER[a]
        # Check if GUI needs updating
        if args.repoGUI is None:
            args.repoGUI = GIT_REPOSITORY_GUI[a]
        if args.localGUI is None:
            args.localGUI = DEFAULT_GUI_FOLDER[a]

    except ValueError:
        print WRONG_VIEW
        return 1


    # Check for updates/clone git OR not
    if args.noCheck:
        # Print warning
        print NO_GIT_CHECK_MSG
    else:
        # Check git for updates
        print "Checking for updates ..."
        status_code = check_updates([args.repoCSV, args.repoCP, args.repoGUI], [args.localCSV, args.localCP, args.localGUI])


    # Return if error occurred while updating
    if status_code != 0:
        print ERROR_UPDATE
        return status_code

    if args.noStart:
        return status_code

    # Launch the correct overview GUI with 2 paths (path to .csv and path to custom GUI files) and a title parameter
    # Create string to start the process with parameters
    start_string = "python2.7 " + str(args.localCP) + "/" + str(OVERVIEW_GUI_NAME) + " --CSV " + str(args.localCSV) + "/" + str(CSV_FILE_NAME[a]) + " --GUI " + str(args.localGUI)
    start_string += " --TITLE " + TITLES[a]
    start_string += " -v " if args.verbose else ""

    # Check if necessary files are in place
    print "\nOpening Control Program ..."
    if not os.path.isfile(str(args.localCP) + "/" + str(OVERVIEW_GUI_NAME)):
        print "File: " + (str(args.localCP) + "/" + str(OVERVIEW_GUI_NAME)) + " does not exist."
        print "Check if the repository location for the Control Program is properly set."
        status_code = 1
    if not os.path.isfile(str(args.localCSV) + "/" + str(CSV_FILE_NAME[a])):
        print "File: " + (str(args.localCSV) + "/" + str(CSV_FILE_NAME[a])) + " does not exist."
        print "Check if the repository location for the CSV files is properly set."
        status_code = 1

    # Return if files not in place
    if status_code != 0:
        print ERROR_RUN_CP
        return status_code

    # Run Control Program
    return subprocess.call(start_string, shell=True)


def check_updates(links, folders):
    import git
    no_errors = 0
    clone_it = False

    # Check if lengths of array match
    if len(links) != len(folders):
        print UNBALANCED_FOLDERS_LINKS
        return 1

    # For each link
    for i in range(len(links)):
        # Check if user has local CSV repo
        try:
            my_csv_repo = git.Repo(folders[i])
            print "Updating: ", my_csv_repo.git_dir

            # Discard any changes and pull new files if needed
            my_csv_repo.index.checkout(None, True)
            my_csv_repo.submodule_update(recursive=True)
            my_csv_repo.remotes.origin.pull()

        except git.InvalidGitRepositoryError:
            # Folder exists but it's not a repository. Create a new one using clone.
            clone_it = True
        except git.exc.NoSuchPathError:
            # There is no folder so create a new repository using clone.
            clone_it = True
        except AssertionError, e:
            # No connection and other problems.
            print "While updating: " + str(links[i]) + " error occurred: " + str(e)
            no_errors += 1
        except Exception, e:
            print "General error: " + str(e)
        except:
            print "Unknown error while trying to update: " + str(links[i])
            no_errors += 1

        # Clone the repo if needed.
        if clone_it:
            clone_it = False
            try:
                print "Cloning from: ", links[i]
                git.Repo.clone_from(links[i], folders[i], branch=GIT_BRANCH, recursive=True)
            except AssertionError, e:
                # No connection and other problems.
                print "While cloning: " + str(links[i]) + " error occurred: " + str(e)
                no_errors += 1
            except:
                print "Unknown error while trying to clone: " + str(links[i])
                no_errors += 1

    return no_errors


if __name__ == '__main__':
    status = main()
    sys.exit(status)
