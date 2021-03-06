import os
import sys
import click
import pathlib
import logging
import calendar
import time
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

from colorama import Fore, Style
from datetime import datetime
from datetime import date



DEFAULT_VERBOSE = False

DEFAULT_OUTDIR = "/tmp/" + os.path.basename(__file__) + '/' + str(datetime.today().strftime('%Y-%m-%d-%H%M%S'))

LOGGING_FORMAT = "%(levelname)s : %(asctime)s : %(pathname)s : %(lineno)d : %(message)s"

LOG_LEVEL = logging.INFO


function_or_method_completer = WordCompleter(['function', 'method'])
yes_or_no_completer = WordCompleter(['yes', 'no'])
datatype_completer = WordCompleter(['bool', 'dict', 'float', 'int', 'list', 'str'])


def generate_function_code_from_file(infile: str = None, outfile: str = None) -> None:
    """Generate the function code from the input file
    :param infile: {str}
    :param outfile: {str}
    :returns None:
    """

    logging.info("Going to parse input file '{}'".format(infile))

    function_name = None
    function_type = None
    return_type = None
    parameter_list = []
    parameter_lookup = {}

    with open(infile, 'r') as fh:

        for line in fh:

            line = line.strip()
            
            if line.startswith('#'):
                continue
            if line.startswith('function_name:'):
                function_name = line.replace('function_name:', '')
                continue
            if line.startswith('function_type:'):
                function_type = line.replace('function_type:', '')
                continue
            if line.startswith('return_type:'):
                return_type = line.replace('return_type:', '')
                continue
            if line.startswith('param:'):
                logging.info("Found param line '{}'".format(line))
                param = line.replace('param:', '')
                parts = param.split(':')
                param_name = parts[0]
                datatype = parts[1]
                default = parts[2]
                desc = parts[3]
                logging.info("Found param '{}' datatype '{}' default '{}' description '{}'".format(param_name, datatype, default, desc))
                if param_name in parameter_lookup:
                    logging.warning("parameter '{}' was already encountered - going to ignore it now".format(param_name))
                    print("parameter '{}' was already encountered - going to ignore it now".format(param_name))
                    continue
                else:
                    parameter_lookup[param_name] = {}
                    parameter_list.append(param_name)
                parameter_lookup[param_name]['datatype'] = datatype
                parameter_lookup[param_name]['default'] = default
                parameter_lookup[param_name]['description'] = desc

    write_function(function_name, function_type, parameter_list, parameter_lookup, return_type, outfile)


def get_function_name() -> str:
    """Prompt the user for the name of the function
    :returns function_name: {str}
    """

    function_name = None

    while function_name is None or function_name == '':
        function_name = input("What is the name of the function? ")
        function_name = function_name.strip()
        if function_name is None or function_name == '':
            continue
        else:
            break

    return function_name


def get_function_type() -> None:
    """Prompt the user for the type of function
    i.e.: function or method
    :return function_type: {str}
    """

    function_type = None # function or method

    while function_type is None or function_type == '':
        function_type = prompt('Is this a function or method? [(f)unction|(m)ethod] ', completer=function_or_method_completer)
        function_type = function_type.strip()
        if function_type is None or function_type == '':
            continue
        if function_type.lower() == 'f' or function_type.lower() == 'function':
            function_type = 'function'
            break
        elif function_type.lower() == 'm' or function_type.lower() == 'method':
            function_type = 'method'
            break
        else:
            function_type = None

    return function_type


def get_return_type() -> None:
    """Prompt the user for the return datatype of the function
    :return return_type: {str}
    """

    return_type = None # function or method

    while return_type is None or return_type == '':
        return_type = prompt("return type? [bool|dict|float|int|list|str]: ", completer=datatype_completer)
        return_type = return_type.strip()
        if return_type is None or return_type == '':
            return_type = 'None'
        break

    return return_type


def generate_function_code(outfile: str = None) -> None:
    """Generate the function code
    :param outfile: {str}
    :returns None:
    """

    has_parameters = None

    parameter_list = []
    parameter_lookup = {}

    run = True

    while run:

        function_name = get_function_name()
        function_type = get_function_type()
        return_type = get_return_type()

        while has_parameters is None or has_parameters == '':
            has_parameters = prompt('Has parameter(s)? [(Y)es|(n)o] ', completer=yes_or_no_completer)
            if has_parameters is None or has_parameters == '':
                has_parameters = 'y'
            break

        if has_parameters.lower() == 'y':

            more_parameters = True

            while more_parameters:

                parameter_name = None
                while parameter_name is None:
                    parameter_name = input("parameter name? ")
                    if parameter_name is None or parameter_name == '':
                        continue
                    else:
                        parameter_name = parameter_name.strip()
                        if parameter_name in parameter_lookup:
                            print(Fore.YELLOW + "parameter name '{}' already exists".format(parameter_name))
                            continue
                        else:
                            parameter_list.append(parameter_name)
                            parameter_lookup[parameter_name] = {}
                            break

                parameter_datatype = None
                while parameter_datatype is None:
                    parameter_datatype = prompt("datatype? [bool|dict|float|int|list|str]: ", completer=datatype_completer)
                    if parameter_datatype is None or parameter_datatype == '':
                        continue
                    else:
                        parameter_datatype = parameter_datatype.strip()
                        parameter_lookup[parameter_name]['datatype'] = parameter_datatype
                        break

                parameter_default = None
                while parameter_default is None:
                    parameter_default = input("default value? [None]: ")
                    if parameter_default is None or parameter_default == '':
                        parameter_default = 'None'
                    else:
                        parameter_default = parameter_default.strip()
                    parameter_lookup[parameter_name]['default'] = parameter_default
                    break

                parameter_description = None
                while parameter_description is None:
                    parameter_description = input("description?: ")
                    if parameter_description is None or parameter_description == '':
                        continue
                    else:
                        parameter_description = parameter_description.strip()
                    parameter_lookup[parameter_name]['description'] = parameter_description
                    break

                more_parameters = input("\nAdd another parameter? [(Y)es|(n)o]: ")
                more_parameters = more_parameters.strip()
                if more_parameters is None or more_parameters == '':
                    more_parameters = 'y'
                if more_parameters.lower() == 'y' or more_parameters.lower() == 'yes':
                    more_parameters = True
                else:
                    more_parameters = False
        run = False

    write_function(function_name, function_type, parameter_list, parameter_lookup, return_type, outfile)


def write_function(function_name, function_type, parameter_list, parameter_lookup, return_type, outfile):
    """Write the function code to the output file
    :param function_name: {str}
    :param function_type: {str}
    :param parameter_list: {list}
    :param parameter_lookup: {dict}
    :param return_type: {str}
    :param outfile: {str}
    """
    formatted_param_list = []
    formatted_param_desc_list = []

    if len(parameter_list) > 0:
        for parameter_name in parameter_list:
            datatype = parameter_lookup[parameter_name]['datatype']
            default = parameter_lookup[parameter_name]['default']
            description = parameter_lookup[parameter_name]['description']
            formatted_param_list.append('{}: {} = {}'.format(parameter_name, datatype, default))
            formatted_param_desc_list.append(':param {}: {{{}}} - {}'.format(parameter_name, datatype, description))

    formatted_param_desc_list.append(':returns var: {{{}}} - '.format(return_type))

    content = []

    if function_type == 'method':
        content.append('def {}(self, '.format(function_name))
    else:
        content.append('def {}('.format(function_name))

    content.append("{}) -> {}:\n".format(", ".join(formatted_param_list), return_type))
    content.append("    '''\n")
    content.append("    {}\n".format("\n    ".join(formatted_param_desc_list)))
    content.append("    '''\n")

    for parameter_name in parameter_list:
        if 'file' in parameter_name:
            if 'outfile' in parameter_name:
                continue
            else:
                content.append("    if {} is None or {} == '':\n".format(parameter_name, parameter_name))
                content.append("        logging.error('{}' is not defined)\n".format(parameter_name))
                content.append("        sys.exit(1)\n")
                content.append("    if not os.path.exists({}):\n".format(parameter_name))
                content.append("        logging.error(file '{}' does not exist)\n".format(parameter_name))
                content.append("        sys.exit(1)\n")

    if not return_type == 'None':
        content.append("\n    return var\n")

    with open(outfile, 'w') as fh:
        for line in content:
            fh.write(line)

    print("\nWrote function defintion to output file '{}'".format(outfile))
    print("Try:\ncat {}".format(outfile))


@click.command()
@click.option('--outdir', help='The output directory - default is {}'.format(DEFAULT_OUTDIR))
@click.option('--outfile', help='The output file - if not specified a default will be assigned')
@click.option('--infile', help='The input file')
@click.option('--logfile', help="The log file - if not is specified a default will be assigned")
@click.option('--verbose', is_flag=True, help="Whether to execute in verbose mode - default is {}".format(DEFAULT_VERBOSE))
def main(outdir, outfile, infile, logfile, verbose):
    """Prompt the user and generate a Python function code
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
        outfile = os.path.join(outdir, infile_basename + '.json')
        print(Fore.YELLOW + "--outfile was not specified and therefore was set to '{}'".format(outfile))
        print(Style.RESET_ALL + '', end='')

    assert isinstance(outfile, str)


    logging.basicConfig(filename=logfile,
                    format=LOGGING_FORMAT,
                    level=LOG_LEVEL)

    if infile is not None and infile != '':
        if not os.path.exists(infile):
            print(Fore.RED + "infile '{}' does not exist".format(infile))
            print(Style.RESET_ALL + '', end='')
            sys.exit(1)
    
        generate_function_code_from_file(infile, outfile)
    else:
        generate_function_code(outfile)


if __name__ == "__main__":
    main()