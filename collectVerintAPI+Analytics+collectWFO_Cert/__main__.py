import sys

from main_start import main_start
def main(args=None):
    """The main routine."""
    if args is None:
        args = sys.argv[1:]

    print("This is the main routine handoff")
    main_start()

    # Do argument parsing here (eg. with argparse) and anything else
    # you want your project to do. Return values are exit codes.


if __name__ == "__main__":
    print("This is the main routine kickoff .")
    main()