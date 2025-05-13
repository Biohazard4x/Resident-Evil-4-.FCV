
# run_fcv.py 
# Terminal Display stuff

import sys
from FCV.fcv_parser import FCVParser

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_fcv.py <path_to_fcv_file> [-verbose]")
        return

    filepath = sys.argv[1]
    verbose = "-verbose" in sys.argv

    parser = FCVParser(filepath, verbose=verbose)
    parser.parse()

    info = parser.get_summary()

    print(f"=== FCV File: {filepath} ===")
    print(f"Max Time    : {info['max_time']} frames")
    print(f"Node Count  : {info['node_count']}")
    print(f"File Size   : {info['file_size']} bytes")
    print(f"Padding     : {info['padding']} byte(s)")
    print(f".FCV parsing complete. See debug .log file for details.")

if __name__ == "__main__":
    main()
