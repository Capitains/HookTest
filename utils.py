import os
import glob

def find_files(directory):
    data = glob.glob(os.path.join(directory, "data/*/*/*.xml")) + glob.glob(os.path.join(directory, "data/*/*.xml"))
    return [f for f in data if "__cts__.xml" not in f], [f for f in data if "__cts__.xml" in f]