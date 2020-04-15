import re
import os
import sys
import click
import pathlib
import logging
import calendar
import time

from colorama import Fore, Style
from datetime import datetime
from datetime import date


DEFAULT_VERBOSE = False

DATE = str(datetime.today().strftime('%Y-%m-%d-%H%M%S'))

DEFAULT_OUTDIR = "/tmp/" + os.path.basename(__file__) + '/' + DATE

DEFAULT_INDIR = os.path.dirname(os.path.abspath(__file__))

LOGGING_FORMAT = "%(levelname)s : %(asctime)s : %(pathname)s : %(lineno)d : %(message)s"

LOG_LEVEL = logging.INFO


def get_file_list(indir: str = None) -> list:
    """Get the list of files in the specified directory.
    Ignore any files in the venv directory.
    :param indir: {str}
    :returns file_list: {list}
    """
    file_ctr = 0
    file_list = []
    for path, subdirs, files in os.walk(indir):
        for name in files:
           file_ctr += 1
           file_path = os.path.join(path, name)
           if 'venv' in file_path or '.git' in file_path:
               logging.info("Ignoring file '{}'".format(file_path))
               continue
           file_list.append(file_path)

    print("Processed '{}' files in directory '{}'".format(file_ctr, indir))
    return file_list

def analyze_code(indir, outdir, outfile):
    """Analyze the code files in the specified directory
    and then generate a summary report.
    :param indir: {str}
    :param outdir: {str}
    :param outfile: {str}
    """
    file_list = get_file_list(indir)

    code_file_ctr = 0
    comment_ctr = 0
    class_ctr = 0
    todo_ctr = 0
    init_file_ctr = 0
    def_ctr = 0
    import_ctr = 0
    from_ctr = 0
    line_ctr = 0
    blank_line_ctr = 0

    for file in file_list:
        logging.info("Going to analyze file '{}'".format(file))

        if os.path.basename(file) == '__init__.py':
            init_file_ctr += 1
            continue

        code_file_ctr += 1
        with open(file, 'r') as fh:
            for line in fh:
                line_ctr += 1
                line = line.strip()
                if re.match(r'^\s*$', line):
                    blank_line_ctr += 1
                    continue

                if re.match(r'^\s*class', line):
                    class_ctr += 1

                if re.match(r'^\s*#\s*TODO', line):
                    todo_ctr += 1

                if re.match(r'^\s*def\s+', line):
                    def_ctr += 1

                if re.match(r'^import', line):
                    import_ctr += 1

                if re.match(r'^from', line):
                    from_ctr += 1

                if re.match(r'^\s*#', line):
                    comment_ctr += 1


    with open(outfile, 'w') as fh:
        fh.write("## method-created: '{}'\n".format(os.path.abspath(__file__)))
        fh.write("## date-created: '{}'\n".format(DATE))
        fh.write("## indir: '{}'\n".format(indir))
        fh.write("code files: '{}'\n".format(code_file_ctr))
        fh.write("__init__.py files: '{}'\n".format(init_file_ctr))
        fh.write("comments '{}'\n".format(comment_ctr))
        fh.write("classes: '{}'\n".format(class_ctr))
        fh.write("TODOs: '{}'\n".format(todo_ctr))
        fh.write("functions: '{}'\n".format(def_ctr))
        fh.write("imports: '{}'\n".format(import_ctr))
        fh.write("from imports: '{}'\n".format(from_ctr))
        fh.write("lines: '{}'\n".format(line_ctr))
        fh.write("blank lines: '{}'\n".format(blank_line_ctr))

    print("Wrote summary report file '{}'".format(outfile))
    logging.info("Wrote summary report file '{}'".format(outfile))


@click.command()
@click.option('--outdir', help='The output directory - default is {}'.format(DEFAULT_OUTDIR))
@click.option('--outfile', help='The output file - if not specified a default will be assigned')
@click.option('--indir', help="'The input directory - default is the current working directory {}".format(DEFAULT_INDIR))
@click.option('--logfile', help="The log file - if not is specified a default will be assigned")
@click.option('--verbose', is_flag=True, help="Whether to execute in verbose mode - default is {}".format(DEFAULT_VERBOSE))
def main(outdir, outfile, indir, logfile, verbose):
    """Analyze the code-base in the specified directory and generate a summary report
    """

    error_ctr = 0

    if error_ctr > 0:
        print(Fore.RED + "Required command-line arguments were not specified")
        print(Style.RESET_ALL + '', end='')
        sys.exit(1)

    if verbose is None:
        verbose = DEFAULT_VERBOSE
        print(Fore.YELLOW + "--verbose was not specified and therefore was set to default '{}'".format(verbose))
        print(Style.RESET_ALL + '', end='')

    assert isinstance(verbose, bool)

    if outdir is None:
        outdir = DEFAULT_OUTDIR
        print(Fore.YELLOW + "--outdir was not specified and therefore was set to default '{}'".format(outdir))
        print(Style.RESET_ALL + '', end='')

    assert isinstance(outdir, str)

    if not os.path.exists(outdir):
        pathlib.Path(outdir).mkdir(parents=True, exist_ok=True)
        print(Fore.YELLOW + "Created output directory '{}'".format(outdir))
        print(Style.RESET_ALL + '', end='')

    infile_basename = os.path.splitext(os.path.basename(__file__))[0]

    if logfile is None:
        logfile = os.path.join(outdir, infile_basename + '.log')
        print(Fore.YELLOW + "--logfile was not specified and therefore was set to '{}'".format(logfile))
        print(Style.RESET_ALL + '', end='')

    assert isinstance(logfile, str)

    if outfile is None:
        outfile = os.path.join(outdir, infile_basename + '.txt')
        print(Fore.YELLOW + "--outfile was not specified and therefore was set to '{}'".format(outfile))
        print(Style.RESET_ALL + '', end='')

    assert isinstance(outfile, str)

    if indir is None:
        indir = DEFAULT_INDIR
        print(Fore.YELLOW + "--indir was not specified and therefore was set to default '{}'".format(indir))
        print(Style.RESET_ALL + '', end='')

    assert isinstance(indir, str)

    logging.basicConfig(filename=logfile,
                    format=LOGGING_FORMAT,
                    level=LOG_LEVEL)

    analyze_code(indir, outdir, outfile)

if __name__ == "__main__":
    main()