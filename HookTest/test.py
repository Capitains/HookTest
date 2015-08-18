# -*- coding: utf-8 -*-

from collections import defaultdict
from sys import argv, stdout, exit
import subprocess
import time
import concurrent.futures

import utils
import units
import json
import statistics

PNRT_SETTINGS = {
    "directory" : "",
    "reponame" : ""
}

def cover(test):
    """ Given a dictionary, compute the coverage of one item 

    :param test: Dictionary where keys represents test done on a file and value a boolean indicating passing status 
    :type test: boolean

    :returns: Passing status 
    :rtype: dict

    """ 
    results = list(test.values())
    return {
        "units" : test,
        "coverage" : len([v for v in results if v is True])/len(results)*100,
        "status" : False not in results
    }

def prnt(data):
    """ Print data and flush the stdout to be able to retrieve information line by line on another tool

    :param data: Data to be printed
    :type data: str

    """
    print(data.replace(PNRT_SETTINGS["directory"], PNRT_SETTINGS["reponame"]), flush=True)


def do_test(f, tei, epidoc, verbose, inventory, results, passing):
    """ Do test for a file and print the results

    :param f: Path of the file to be tested
    :type f: str

    :returns: List of status informations
    :rtype: list
    """
    logs = []
    if not inventory:
        inventory = []
    if f.endswith("__cts__.xml"):
        t = units.INVUnit(f)
        logs.append(">>>> Testing "+ f)

        for name, status, op in t.test():
            
            if status:
                status_str = " passed"
            else:
                status_str = " failed"

            logs.append(">>>>> " +name + status_str)

            if verbose:
                logs.append("\n".join([o for o in op]))

            results[f][name] = status

        results[f] = cover(results[f])
        passing[f.replace("/", ".")] = True == results[f]["status"]
        inventory += t.urns

    else:
        t = units.CTSUnit(f)
        logs.append(">>>> Testing "+ f.split("data")[-1])
        for name, status, op in t.test(tei, epidoc, inventory):
            
            if status:
                status_str = " passed"
            else:
                status_str = " failed"

            logs.append(">>>>> " +name + status_str)

            if verbose:
                logs.append("\n".join([o for o in op]))

            results[f][name] = status

        results[f] = cover(results[f])
        passing[f.split("/")[-1]] = True == results[f]["status"]

    return logs + ["test+=1"], inventory, results, passing

def run(opts, uuid, reponame, branch, dest):
    """ Run the tests

    :param opts: Options (-vte)
    :type opts: str
    :param uuid: Identifier of the test
    :type uuid: str
    :param reponame: Name of the Git Repository
    :type reponame: str
    :param branch: Identifier of the branch
    :type branch: str
    :param dest: Folder containing the repository
    :type dest: str

    :returns: Boolean indicating success
    :rtype: boolean
    """
    ###
    ###    Initialization and parameters recovering
    ###
    errors = False
    inv = []

    PNRT_SETTINGS["directory"] = "/".join([dest, uuid])
    PNRT_SETTINGS["reponame"] = reponame

    if len(opts) > 1:
        opts = list(opts[1:])
    else:   
        opts = list()

    verbose = "v" in opts
    tei = "t" in opts
    epidoc = "e" in opts

    """ 
        Results storing variables initialization
    """

    # Store the results
    results = defaultdict(dict)
    passing = defaultdict(dict)

    files, cts__ = utils.find_files(PNRT_SETTINGS["directory"])

    prnt(">>> Starting tests !")
    prnt("files="+str(len(files) + len(cts__)))

    # We load a thread pool which has 5 maximum workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # We create a dictionary of tasks which 
        tasks = {executor.submit(do_test, target_file, tei, epidoc, verbose, inv, results, passing): target_file for target_file in cts__}
        # We iterate over a dictionary of completed tasks
        for future in concurrent.futures.as_completed(tasks):
            logs, inv, results, passing = future.result()
            for log in logs:
                prnt(log)

    # We load a thread pool which has 5 maximum workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # We create a dictionary of tasks which 
        tasks = {executor.submit(do_test, target_file, tei, epidoc, verbose, inv, results, passing): target_file for target_file in files}
        # We iterate over a dictionary of completed tasks
        for future in concurrent.futures.as_completed(tasks):
            logs, inv, results, passing = future.result()
            for log in logs:
                prnt(log)

    prnt(">>> Finished tests !")

    success = len([True for status in passing.values() if status is True])
    if success == len(passing):
        status_string = "success"
    else:
        status_string = "failure"
    prnt("[{2}] {0} over {1} texts have fully passed the tests".format(success, len(passing), status_string))

    prnt("====JSON====")
    prnt(json.dumps({
        "status" : success == len(passing),
        "units" : results,
        "coverage" : statistics.mean([test["coverage"] for test in results.values()])
    }))

    return success == len(passing)

if __name__ == '__main__':
    if run(*argv[1:]) is False:
        exit(1)
    else:
        exit(0)
