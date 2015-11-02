# -*- coding: utf-8 -*-


"""gflow.gflow: provides entry point main()."""


__version__ = "0.2.0"


import getopt
import sys
import ConfigParser
from bioblend import galaxy


def print_usage(outstream):
  usage = ("Usage: gflow.py [options] config.txt\n"
           "  Options:\n"
           "    -h|--help           print this help message and exit")
  print >> outstream, usage


def read_config(configfile):
  config = ConfigParser.RawConfigParser()
  config.read(configfile)
  options = dict()
  options['galaxy_url'] = config.get('galaxy', 'galaxy_url')
  options['galaxy_key'] = config.get('galaxy', 'galaxy_key')
  options['library_name'] = config.get('library', 'library_name')
  options['dataset_src'] = config.get('input', 'dataset_src')
  options['num_datasets'] = config.get('input', 'num_datasets')
  options['file1'] = config.get('input', 'data1')
  options['output_history_name'] = config.get('output', 'output_history_name')
  options['workflow_src'] = config.get('workflow', 'source')
  options['input_label'] = config.get('workflow', 'input_label')
  options['workflow'] = config.get('workflow', 'workflow')
  return options


def parse_options():
  outstream = sys.stdout

  # Parse options
  optstr   = "h"
  longopts = ["help"]
  (options, args) = getopt.getopt(sys.argv[1:], optstr, longopts)

  for key, value in options:
    if key in ("-h", "--help"):
      print_usage(sys.stdout)
      sys.exit(0)
    else:
      assert False, "ERROR: Unsupported option '%s'" % key

  configfile = None
  instream = None

  if len(args) > 0:
    configfile = args[0]
    try:
      instream = open(configfile, "r")
    except IOError as e:
      print >> sys.stderr, "ERROR: Opening config file %s" % configfile
      print >> sys.stderr, e
      sys.exit(1)

  elif not sys.stdin.isatty():
    instream = sys.stdin

  else:
    print >> sys.stderr, "ERROR: Please provide a config file"
    print_usage(sys.stderr)
    sys.exit(1)

  instream.close()

  return configfile


def main():

  configfile = parse_options()

  options = read_config(configfile)

  print("Initiating Galaxy connection")
  gi = galaxy.GalaxyInstance(url=options['galaxy_url'], key=options['galaxy_key'])

  print("Importing workflow")
  if options['workflow_src'] == 'local':
    wf_import_dict = gi.workflows.import_workflow_from_local_path(options['workflow'])
  elif options['workflow_src'] == 'shared':
    wf_import_dict = gi.workflows.import_shared_workflow(options['workflow'])
  elif options['workflow_src'] == 'json':
    wf_import_dict = gi.workflows.import_workflow_json(options['workflow'])
  else:
    print >> sys.stderr, "ERROR: Accepted workflow sources are: local, shared, or json"
    sys.exit(1)
  workflow = wf_import_dict['id']

  print("Creating data library '%s'" % options['library_name'])
  library_dict = gi.libraries.create_library(options['library_name'])
  library = library_dict['id']

  print("Importing data")
  filenames = dict()
  if options['dataset_src'] == 'local':
    dataset1 = gi.libraries.upload_file_from_local_path(library, options['file1'])
  elif options['dataset_src'] == 'server':
    dataset1 = gi.libraries.upload_file_from_server(library, options['file1'])
  elif options['dataset_src'] == 'url':
    dataset1 = gi.libraries.upload_file_from_url(library, options['file1'])
  elif options['dataset_src'] == 'galaxyfs':
    dataset1 = gi.libraries.upload_file_from_galaxy_filesystem(library, options['file1'])
  else:
    print >> sys.stderr, "ERROR: Accepted dataset sources are: local, server, url, or galaxyfs"
  id1 = dataset1[0]['id']
  filenames[id1] = options['file1']

  print("Creating output history '%s'" % options['output_history_name'])
  outputhist_dict = gi.histories.create_history(options['output_history_name'])
  outputhist = outputhist_dict['id']
  input1 = gi.workflows.get_workflow_inputs(workflow, label=options['input_label'])[0]

  print("Initiating workflow run")
  datamap = dict()
  datamap[input1] = {'src': 'ld', 'id': id1}
  result = gi.workflows.run_workflow(workflow, datamap, history_id=outputhist)