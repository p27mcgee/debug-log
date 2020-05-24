#!/usr/bin/env python3

from os import path

SKEWER = "-"

def makeLogPath(dir, log_ext, *signature_names):
    filename = ""
    for signature_name in signature_names:
        if filename:
            filename += SKEWER
        filename += signature_name
    filename += log_ext
    return path.join(dir, filename)

def filter_log(infile, outfile, filter):
    with open(infile, 'r') as inlog:
        with open(outfile, 'w') as outlog:
            incnt = 0
            outcnt = 0
            for line in inlog:
                incnt += 1
                if (filter(line)):
                    outlog.write(line)
                    outcnt += 1
            print("Read {} lines from {}".format(str(incnt), infile))
            print("Wrote {} lines to {}".format(str(outcnt), outfile))

def applyFilters(line, signature_map, *signature_names):
    negate_next_term = False
    result = True
    for signature_name in signature_names:
        if signature_name == NOT:
            negate_next_term = not negate_next_term
            continue
        signature = signature_map[signature_name]
        if negate_next_term:
            result = result and not signature in line
        else:
            result = result and signature in line
        negate_next_filter = False
    return result

def call_filter_log(src_log, output_dir, log_ext, signature_map, *signature_names):
    filter_log(src_log, makeLogPath(output_dir, log_ext, *signature_names), lambda line: applyFilters(line, signature_map, *signature_names))
    print()

NOT = "not"
CLASSLOAD = "classload"
BLACKLISTED = "blacklisted"
NULL_LOADER = "nullloader"
NULL_LOADER_NAME = "nullname"
PLATFORM_LOADER = "platformloader"
APP_LOADER = "apploader"
NULL_PD = "nullpd"
NULL_LOC = "nullloc"

signature_map = {
    CLASSLOAD: "!PM!ClassLoad|",
    BLACKLISTED: "&result=BLACKLISTED",
    NULL_LOADER: "|classloader=NULL_LOADER&",
    NULL_LOADER_NAME: "|classloader=null&",
    PLATFORM_LOADER: "|classloader=platform&",
    APP_LOADER: "|classloader=app&",
    NULL_PD: "&location=NULL_ProtectionDomain",
    NULL_LOC: "&location=null"
}

data_dir = "/Users/philmcgee/GitHub/debug-log/data"
results_dir = "/Users/philmcgee/GitHub/debug-log/results"
log_ext = ".log"
debug_log = makeLogPath(data_dir, log_ext, "petclinic")

logs_signature_names = [
    [CLASSLOAD],
    # [CLASSLOAD, BLACKLISTED],
    # [CLASSLOAD, NOT, BLACKLISTED],
    [CLASSLOAD, NULL_LOADER],
    [CLASSLOAD, NULL_LOADER_NAME],
    [CLASSLOAD, NULL_LOADER, NOT, NULL_PD],
    [CLASSLOAD, NULL_LOADER_NAME, NOT, NULL_PD],
    [CLASSLOAD, NOT, NULL_LOADER, NOT, NULL_LOADER_NAME],
    [CLASSLOAD, NOT, NULL_LOADER],
    [CLASSLOAD, PLATFORM_LOADER],
    [CLASSLOAD, APP_LOADER],
    [CLASSLOAD, NOT, NULL_LOADER, NOT, NULL_LOADER_NAME, NOT, PLATFORM_LOADER, NOT, APP_LOADER]
]

def generate_filtered_logs(logs_signature_names):
    for signature_names in logs_signature_names:
        call_filter_log(debug_log, results_dir, log_ext, signature_map, *signature_names)

generate_filtered_logs(logs_signature_names)

