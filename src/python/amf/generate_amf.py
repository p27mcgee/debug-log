from src.python.amf import agent_getter
from zipfile import ZipFile
import re
import os
import subprocess
import base64

verbose = True

def list_amf_contents(amf_path):
    input_zip = ZipFile(amf_path)
    return input_zip.namelist()

def get_amf_entry(amf_path, entry_name):
    input_zip = ZipFile(amf_path)
    return input_zip.read(entry_name)

def create_amf(agent_path, log_path):
    if verbose:
        print("Current directory " + os.getcwd())
    print("Generating amf in directory " + os.getcwd())

    cmd = ['java', '-jar',  agent_path, 'analyze-log',  log_path, 'amf']
    returned_output = subprocess.check_output(cmd)
    output_str = returned_output.decode('utf-8')
    if verbose:
        print('Executing "{}" returned:\n {}'.format(cmd, output_str))

    lines = output_str.split('\n')
    amf_file = 'Not found.'
    for line in lines:
        if line.startswith("Agent metrics written to "):
            amf_file = line.lstrip("Agent metrics written to ").rstrip('\n')
            break
    if verbose:
        print('amf_file: ' + amf_file)
    return amf_file

def summarize_amf(amf_path):
    amf_contents = list_amf_contents(amf_path)
    if verbose:
        print('amf_contents: ' + str(amf_contents))
    print("server: \n" + get_amf_entry(amf_path, 'server.json').decode("utf-8"))
    print("properties: \n" + get_amf_entry(amf_path, 'properties.json').decode("utf-8"))
    print("attributes: " + get_amf_entry(amf_path, 'attributes.json').decode("utf-8"))
    apps = get_amf_entry(amf_path, 'apps.json')
    print("apps.decode(\"utf-8\"): " + apps.decode("utf-8"))
    print("apps.decode(): " + apps.decode())
    print("apps: " + base64.b64decode(get_amf_entry(amf_path, 'apps.json').decode()).decode("utf-8"))
    print("features: " + get_amf_entry(amf_path, 'features.json').decode("utf-8"))


def main():
    agent_path = agent_getter.get_latest_agent()
    log_path = 'data/san-sb-petclinic.log'
    amf_path = create_amf(agent_path, log_path)
    summarize_amf(amf_path)

if __name__ == '__main__':
    main()