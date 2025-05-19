
# run_fcv.py 
# Terminal Display stuff

import sys
from FCV.fcv_parser import FCVParser

def main():
    if len(sys.argv) < 3:
        print("Usage: python run_FCV.py <path_to_fcv_file> <little|big> [verbose]")
        return

    filepath = sys.argv[1]
    endian_arg = sys.argv[2].lower()
    verbose = "verbose" in sys.argv

    if endian_arg == "little":
        endianness = "<"
    elif endian_arg == "big":
        endianness = ">"
    else:
        print("Invalid endian option. Use 'little' or 'big'.")
        return

    print("=== BEGIN FCV PARSE ===")
    print(f"Endian Mode: {endianness}")
    print(f"Target File: {filepath}")

    parser = FCVParser(filepath, verbose=verbose, endianness=endianness)
    parser.parse()

    info = parser.get_summary()

    print(f"=== FCV File ===")
    print(f"Max Time    : {info['max_time']} frames")
    print(f"Node Count  : {info['node_count']}")
    print(f"File Size   : {info['file_size']} bytes")
    print(f"File Size_F : {info['real_file_size']} bytes") #Displays actual file Size - for insurance   
    print(f"Padding     : {info['padding']} byte(s)")
    print(f".FCV parsing complete. See debug .log file for details.")

if __name__ == "__main__":
    main()
