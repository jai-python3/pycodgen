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

    for panel_attributes in panel_attributes_list:
        
        content = panel_attributes.text
        
        logging.info("content '{}'".format(content))        
        # print("content '{}'".format(content))        
    
        package_name = None
        class_desc = 'INSERT CLASS DESCRIPTION HERE'
        import_list = []
        attribute_list = []
        method_list = []
        
        
        in_attribute_section = False
        in_method_section = False
    
        line_ctr = 0

        for line in content.split("\n"):
            line_ctr += 1
            line = line.strip()
            if line_ctr == 1:
                package_name = line
                logging.info("Found packge name '{}'".format(package_name))
                continue
            if line.startswith('//desc:'):
                class_desc = line.replace('//desc:', '')
                logging.info("Found class description '{}'".format(class_desc))
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
        
        print("Parsed '{}' lines".format(line_ctr))

        create_class_definition(package_name, class_desc, import_list, attribute_list, method_list)
            

def create_class_definition(package_name, class_desc, import_list, attribute_list, method_list):
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
        fh.write("\n\n")
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

        for method in method_list:
            method_name, formatted_params, param_desc_list, return_type = get_param_desc_list(method)            
            fh.write("    def {}(self, {}) -> {}:\n".format(method_name, formatted_params, return_type))
            fh.write("        '''INSERT DESCRIPTION HERE\n")
            for param_desc in param_desc_list:
                fh.write("        :param {}: {{{}}} -\n".format(param_desc['param_name'], param_desc['datatype']))
            fh.write("        '''\n\n")

def get_param_desc_list(line):
    """
    """
    logging.info("Going to derive parameter details from method definition '{}'".format(line))
    split1 = line.split('(')
    split2 = split1[1].split(')')
    split3 = split2[0].split(',')
    
    param_details_list = []
    params = []
    for param_details in split3:
        param_name, type_default = param_details.split(':')
        param_name = param_name.strip()
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
    
    return method_name, formatted_params, param_details_list, return_type



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