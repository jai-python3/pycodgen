import os
import sys
import click
import pathlib
import logging
import shutil
import calendar
import time
import xml.etree.ElementTree as ET

from pathlib import Path
from colorama import Fore, Style
from datetime import datetime
from datetime import date

DEFAULT_VERBOSE = False

DEFAULT_OUTDIR = "/tmp/" + os.path.basename(__file__) + '/' + str(datetime.today().strftime('%Y-%m-%d-%H%M%S'))

LOGGING_FORMAT = "%(levelname)s : %(asctime)s : %(pathname)s : %(lineno)d : %(message)s"

LOG_LEVEL = logging.INFO


def get_panel_attributes_list(infile: str = None) -> list:
    """
    """
    tree = ET.parse(infile)
    root = tree.getroot()
    panel_attributes_list = []
    for panel_attributes in root.iter('panel_attributes'):
        panel_attributes_list.append(panel_attributes)

    return panel_attributes_list

def convert(infile: str = None, outfile: str = None) -> None:
    """Parse the Umlet .uxf XML file and generate the code
    :param infile: {str}
    :param outfile: {str}
    :returns None:
    """
    panel_attributes_list = get_panel_attributes_list(infile)

    for pa_attrib_ctr, panel_attributes in enumerate(panel_attributes_list, 1):
        
    
        content = panel_attributes.text
        
        logging.info("Here is the content for panel_attributes number '{}' '{}'".format(content, pa_attrib_ctr))        
        # print("content '{}'".format(content))        
    
        package_name = None
        class_desc = 'INSERT CLASS DESCRIPTION HERE'
        import_list = []
        attribute_list = []
        method_list = []
        inherits_from_class = None
        is_singleton = False
        
        in_attribute_section = False
        in_method_section = False
    
        line_ctr = 0

        for line in content.split("\n"):
            line_ctr += 1
            line = line.strip()
            if line_ctr == 1:
                package_name = line
                logging.info("Found package name '{}'".format(package_name))
                continue
            if line.startswith('//singleton'):
                is_singleton = True
                logging.info("Found indication that this class is a singleton")
                continue
            if line.startswith('//desc:'):
                class_desc = line.replace('//desc:', '')
                logging.info("Found class description '{}'".format(class_desc))
                continue
            if line.startswith('//inherits:'):
                inherits_from_class = line.replace('//inherits:', '')
                logging.info("Found inherits '{}'".format(inherits_from_class))
                continue
            if line.startswith('//import') or line.startswith('//from'):
                line = line.replace('//', '')
                logging.info("Found import '{}'".format(line))
                import_list.append(line)
                continue
            if line.startswith('--'):
                if in_attribute_section:
                    logging.info("Found method section")
                    in_method_section = True
                    in_attribute_section = False
                else:
                    logging.info("Found attribute section")
                    in_attribute_section = True
                    in_method_section = False
                continue
            if in_attribute_section:
                attribute_list.append(line)
                logging.info("Found attribute '{}'".format(line))
                continue
            elif in_method_section:
                if len(line) > 5:
                    method_list.append(line)
                    logging.info("Found method '{}'".format(line))
                else:
                    logging.info("Going to ignore method line '{}' at line number '{}'".format(line, line_ctr))
                continue
            else:
                logging.error("Don't know what to do with '{}' at line number '{}'".format(line, line_ctr))
                continue
        
        print("Parsed '{}' lines in panel_attributes number '{}' for package '{}'".format(line_ctr, pa_attrib_ctr, package_name))

        create_class_definition(package_name, class_desc, inherits_from_class, import_list, attribute_list, method_list, is_singleton)
            

def create_class_definition(package_name, class_desc, inherits_from_class, import_list, attribute_list, method_list, is_singleton):
    """
    """
    path = package_name.split('.')
    class_name = path[-1]

    logging.info("class name '{}'".format(class_name))
    filename = path[-2]
    
    logging.info("filename '{}'".format(filename))

    count = len(path)
    dirname_list = []
    for i, dir in enumerate(path):
        if i < count - 2:
            dirname_list.append(dir)
    dirname = '/'.join(dirname_list)
    
    logging.info("dirname '{}'".format(dirname))

    if not os.path.exists(dirname):
        pathlib.Path(dirname).mkdir(parents=True, exist_ok=True)

    cumulative_path = ''
    for dir in dirname_list:
        cumulative_path += dir + '/'
        file = cumulative_path + '__init__.py'
        logging.info("Will check for file '{}'".format(file))
        if not os.path.exists(file):
            Path(file).touch()
            logging.info("touched file '{}'".format(file))

    outfile = os.path.join(dirname, filename + '.py')        
    if os.path.exists(outfile):
        bak_file = outfile + '.bak'
        shutil.move(outfile, bak_file)
        logging.info("Backed up outfile '{}' to '{}'".format(outfile, bak_file))

    with open(outfile, 'w') as fh:
        for line in import_list:
            fh.write("{}\n".format(line))

        if is_singleton:
            fh.write("from singleton_decorator import singleton\n")

        if inherits_from_class is not None:
            # E.g.: inherits_from_class = some.package.namespace.Converter

            inherits_parts = inherits_from_class.split('.')
            # e.g.: inherits_parts will be ['some', 'package', 'namespace', 'Converter']

            base_class_name = inherits_parts[-1] 
            # e.g.: base_class_name will be Converter
            
            inherits_import = inherits_from_class.replace('.' + base_class_name, '')  
            # e.g.: inherits_import will be some.package.namespace

            fh.write("from {} import {}\n".format(inherits_import, base_class_name))

            fh.write("\n\n")

            if is_singleton:
                fh.write("@singleton\n")

            fh.write("class {}({}):\n".format(class_name, base_class_name))
        else:
            fh.write("\n\n")

            if is_singleton:
                fh.write("@singleton\n")

            fh.write("class {}():\n".format(class_name))

        fh.write("    '''{}\n".format(class_desc))
        fh.write("    '''\n\n")
        fh.write("    def __init__(self, **kwargs):\n")
        fh.write("        '''Class constructor\n")
        fh.write("        '''\n\n")
        for attribute in attribute_list:
            logging.info("Process attribute '{}'".format(attribute))
            fh.write("        if '{}' in kwargs:\n".format(attribute))
            fh.write("            self._{} = kwargs['{}']\n\n".format(attribute, attribute))
        fh.write("\n")

        insert_check_file_status_private_method = False

        for method in method_list:
            method_name, formatted_params, param_desc_list, return_type, params_name_list = get_param_desc_list(method)            
            fh.write("    def {}(self, {}) -> {}:\n".format(method_name, formatted_params, return_type))
            fh.write("        '''INSERT DESCRIPTION HERE\n")
            for param_desc in param_desc_list:
                fh.write("        :param {}: {{{}}} -\n".format(param_desc['param_name'], param_desc['datatype']))
            fh.write("        '''\n\n")

            for param_name in params_name_list:
                if 'file' in param_name:
                    if 'outfile' not in param_name:
                        fh.write("        self._check_infile_status({})\n\n".format(param_name))
                        insert_check_file_status_private_method = True


        #! Move this to a Jinja2 template soon
        fh.write("    def _check_infile_status(self, infile: str = None) -> None:\n")
        fh.write("        '''Check the input file for the following:\n")
        fh.write("        1) does the file variable defined\n")
        fh.write("        2) does the file exist\n")
        fh.write("        3) does the file a regular file or a file symlink\n")
        fh.write("        4) does the file have content\n")
        fh.write("        :param infile: {str} - input file to check status of\n")
        fh.write("        '''\n\n")
        fh.write("        if {} is None or {} == '':\n".format(param_name, param_name))
        fh.write("            logging.error(\"'{{}}' is not defined'\".format({}))\n".format(param_name))
        fh.write("            sys.exit(1)\n\n")
        fh.write("        if not os.path.exists({}):\n".format(param_name))
        fh.write("            logging.error(\"file '{{}}' does not exist'\".format({}))\n".format(param_name))
        fh.write("            sys.exit(1)\n\n")
        fh.write("        if not os.path.isfile({}):\n".format(param_name))
        fh.write("            logging.error(\"'{{}}' is not a regular file or a symlink to a file\".format({}))\n".format(param_name))
        fh.write("            sys.exit(1)\n\n")
        fh.write("        if not os.stat({}) == 0:\n".format(param_name))
        fh.write("            logging.error(\"file '{{}}' has no content\".format({}))\n".format(param_name))
        fh.write("            sys.exit(1)\n\n")


    
    print("Wrote output file '{}'".format(outfile))


def get_param_desc_list(line):
    """
    """
    logging.info("Going to derive parameter details from method definition '{}'".format(line))
    split1 = line.split('(')
    split2 = split1[1].split(')')
    split3 = split2[0].split(',')
    
    param_details_list = []
    params = []
    params_name_list = []
    for param_details in split3:
        param_name, type_default = param_details.split(':')
        param_name = param_name.strip()
        params_name_list.append(param_name)
        datatype, default = type_default.split('=')
        datatype = datatype.strip()
        default = default.strip()
        param_details_list.append({'param_name': param_name, 'datatype': datatype, 'default': default})
        params.append('{}: {} = {}'.format(param_name, datatype, default))

    formatted_params = ', '.join(params)
    method_name = split1[0].strip()
    return_type = split2[1].strip()
    if return_type.startswith('->'):
        return_type =  return_type.replace('->', '')
    if return_type.endswith(':'):
        return_type =  return_type.replace(':', '')
    
    return method_name, formatted_params, param_details_list, return_type, params_name_list



@click.command()
@click.option('--outdir', help='The output directory - default is {}'.format(DEFAULT_OUTDIR))
@click.option('--outfile', help='The output file - if not specified a default will be assigned')
@click.option('--infile', help='The input file - should be the Umlet .uxf XML file')
@click.option('--logfile', help="The log file - if not is specified a default will be assigned")
@click.option('--verbose', is_flag=True, help="Whether to execute in verbose mode - default is {}".format(DEFAULT_VERBOSE))
def main(outdir, outfile, infile, logfile, verbose):
    """Parses the Umlet .uxf XML file and generates the Python API code
    """

    error_ctr = 0

    if infile is None:
        print(Fore.RED + "--infile was not specified")
        print(Style.RESET_ALL + '', end='')
        error_ctr += 1

    if error_ctr > 0:
        print(Fore.RED + "Required command-line arguments were not specified")
        print(Style.RESET_ALL + '', end='')
        sys.exit(1)

    assert isinstance(infile, str)

    if not os.path.exists(infile):
        print(Fore.RED + "'{}' does not exist".format(infile))
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

    infile_basename = os.path.splitext(os.path.basename(infile))[0]

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

    convert(infile, outfile)


if __name__ == "__main__":
    main()