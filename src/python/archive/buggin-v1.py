#!/usr/bin/env python3

from os import path
from functools import reduce
import operator

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


data_dir = "/Volumes/GoogleDrive/My Drive/work/PycharmProjects/debug-logs/data/"
log_ext = ".log"
skewer = "-"

def makeLogPath(*signature_names):
    filename = ""
    for signature_name in signature_names:
        if filename:
            filename += skewer
        filename += signature_name
    filename += log_ext
    return path.join(data_dir, filename)

NOT = "not"
CLASSLOAD = "classload"
BLACKLISTED = "blacklisted"
NULLLOADER = "nullloader"
NULLLPD = "nullpd"

signature_map = {
    CLASSLOAD: "!PM!ClassLoad|",
    BLACKLISTED: "|classloader=BLACKLISTED&location=BLACKLISTED",
    NULLLOADER: "|classloader=NULL_LOADER&",
    NULLLPD: "&location=NULL_ProtectionDomain"
}

filter_map = {
    CLASSLOAD: lambda line: signature_map[CLASSLOAD] in line,
    BLACKLISTED: lambda line: signature_map[BLACKLISTED]  in line
}

# infinite loop recursion
# def filterFactory(signature_map, *signature_names):
#     negate_next_term = False
#     filter_terms = []
#     for signature_name in signature_names:
#         if signature_name == NOT:
#             negate_next_term = not negate_next_term
#             continue
#         signature = signature_map[signature_name]
#         if negate_next_term:
#             term = lambda line: not signature in line
#         else:
#             term = lambda line: signature in line
#         filter_terms.append(term)
#         negate_next_filter = False
#     return lambda line: reduce()

def applyFilters(line, *signature_names):
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

debug_log = makeLogPath("petclinic")

def call_filter_log(*signature_names):
    filter_log(debug_log, makeLogPath(*signature_names), lambda line: applyFilters(line, *signature_names))
    print()

logs_signature_names = [
    [CLASSLOAD],

    [CLASSLOAD, BLACKLISTED],
    [CLASSLOAD, NOT, BLACKLISTED]
]

for signature_names in logs_signature_names:
    call_filter_log(*signature_names)

# filter_log(debug_log, makeLogPath(CLASSLOAD, BLACKLISTED), lambda line: applyFilters(line, CLASSLOAD, BLACKLISTED))
# filter_log(debug_log, makeLogPath(CLASSLOAD, NOT, BLACKLISTED), lambda line: applyFilters(line, CLASSLOAD, NOT, BLACKLISTED))

# filter_log(debug_log, makeLogPath(CLASSLOAD, BLACKLISTED), lambda line: applyFilters(line, CLASSLOAD, BLACKLISTED))
# filter_log(debug_log, makeLogPath(CLASSLOAD, NOT, BLACKLISTED), lambda line: applyFilters(line, CLASSLOAD, NOT, BLACKLISTED))
# print()


# def nullloader_nullpd_filter(line):
#     return "|classloader=NULL_LOADER&location=NULL_ProtectionDomain" in line
#
# nullloader_nullpd_loads = "/Volumes/GoogleDrive/My Drive/work/PycharmProjects/debug-logs/data/nullloader-nullpd-loads.log"
# not_nullloader_nullpd_loads = "/Volumes/GoogleDrive/My Drive/work/PycharmProjects/debug-logs/data/not-nullloader-nullpd-loads.log"
# filter_log(classload_not_blacklisted_log, nullloader_nullpd_loads, nullloader_nullpd_filter)
# filter_log(classload_not_blacklisted_log, not_nullloader_nullpd_loads, lambda line: not nullloader_nullpd_filter(line))
# print()
#
# def nullname_nullpd_filter(line):
#     return "|classloader=null&location=NULL_ProtectionDomain" in line
#
# nullname_nullpd_loads = "/Volumes/GoogleDrive/My Drive/work/PycharmProjects/debug-logs/data/nullname-nullpd-loads.log"
# not_nullname_nullpd_loads = "/Volumes/GoogleDrive/My Drive/work/PycharmProjects/debug-logs/data/not-nullname-nullpd-loads.log"
# filter_log(not_nullloader_nullpd_loads, nullname_nullpd_loads, nullname_nullpd_filter)
# filter_log(not_nullloader_nullpd_loads, not_nullname_nullpd_loads, lambda line: not nullname_nullpd_filter(line))
# print()
#
# def nullname_notnullpd_filter(line):
#     return "|classloader=null&" in line and not "&location=NULL_ProtectionDomain"
#
# nullname_notnullpd_loads = "/Volumes/GoogleDrive/My Drive/work/PycharmProjects/debug-logs/data/nullname-notnullpd-loads.log"
# not_nullname_notnullpd_loads = "/Volumes/GoogleDrive/My Drive/work/PycharmProjects/debug-logs/data/not-nullname-notnullpd-loads.log"
# filter_log(not_nullname_nullpd_loads, nullname_notnullpd_loads, nullname_notnullpd_filter)
# filter_log(not_nullname_nullpd_loads, not_nullname_notnullpd_loads, lambda line: not nullname_notnullpd_filter(line))
# print()
#
# nullname_loads = "/Volumes/GoogleDrive/My Drive/work/PycharmProjects/debug-logs/data/nullname-loads.log"
# platform_loads = "/Volumes/GoogleDrive/My Drive/work/PycharmProjects/debug-logs/data/platform-loads.log"
# app_loads = "/Volumes/GoogleDrive/My Drive/work/PycharmProjects/debug-logs/data/app-loads.log"
# not_null_platform_app_loads = "/Volumes/GoogleDrive/My Drive/work/PycharmProjects/debug-logs/data/not-null-platform-app-loads.log"
# filter_log(not_nullname_notnullpd_loads, nullname_loads, lambda line: "|classloader=null&" in line)
# filter_log(not_nullname_notnullpd_loads, platform_loads, lambda line: "|classloader=platform&" in line)
# filter_log(not_nullname_notnullpd_loads, app_loads, lambda line: "|classloader=app&" in line)
# filter_log(not_nullname_notnullpd_loads, not_null_platform_app_loads, lambda line: not "|classloader=null&" in line and not "|classloader=platform&" in line and not "|classloader=app&" in line)
# print()
