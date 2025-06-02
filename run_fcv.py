
import sys
import os
import struct
import json

from colorama import init, Fore, Style

from FCV.fcv_parser import FCVParser

init(autoreset=True) #Colorama init

def detect_endian(filepath, max_nodes=30):
    """
    Detects the endianness (little or big) of an FCV file by
    evaluating header values and basic sanity checks.

    Args:
        filepath (str): Path to the FCV file.
        max_nodes (int): Maximum number of nodes to read for validation.

    Returns:
        str: '<' for little-endian or '>' for big-endian, depending on the score.
    """

    with open(filepath, "rb") as f:
    # Open the file in binary mode and read enough bytes for:
    # - 2 bytes for max_time
    # - 1 byte for node_count
    # - 2 bytes per node (node_type and data_type)
        data = f.read(3 + max_nodes * 2)

    scores = {}
    for endian in ("<", ">"):
        try:
            max_time = struct.unpack(endian + "H", data[:2])[0]
            node_count = struct.unpack(endian + "B", data[2:3])[0]
            score = 0

            # Check if max_time looks reasonable (1 to 32767 frames)
            if 1 <= max_time <= 32767:
                score += 1
                
            # Check if node_count looks reasonable (1 to 100 nodes)
            if 1 <= node_count <= 100:
                score += 1

            invalid_nodes = 0 # Counter for suspicious node types
            
            # Validate each node's type (node_type field)
            for i in range(min(node_count, max_nodes)):
                base = 3 + i * 2
                b1 = struct.unpack(endian + "B", data[base:base+1])[0]
                b2 = struct.unpack(endian + "B", data[base+1:base+2])[0]
                node_type = b1 if endian == "<" else b2
                
                # Consider node_type == 0 suspicious (invalid)
                if node_type == 0:
                    invalid_nodes += 1
            if invalid_nodes == 0:
                score += 1

            scores[endian] = score
        except:
            scores[endian] = -1

    return max(scores, key=scores.get)

def process_file(filepath, verbose, force_endian=None, export_json=False):
    """
    Processes a single .fcv file: detects endianness (or uses forced),
    parses the file, prints summary info, and optionally exports JSON.

    Args:
        filepath (str): Path to the FCV file.
        verbose (bool): Enable verbose output (debug logging).
        force_endian (str or None): '<' or '>' to force endian mode, otherwise auto-detect.
        export_json (bool): Whether to export parsed data to JSON.

    Returns:
        None on success, or an error message on failure.
    """
    try:
        # Detect or force endianness    
        endianness = force_endian if force_endian else detect_endian(filepath)
        print(Fore.GREEN + "=== BEGIN FCV PARSE ===" + Style.RESET_ALL)
        print(f"Endian Mode: {'Little' if endianness == '<' else 'Big'}")
        print(f"Target File: {filepath}")

        # Initialize the FCV parser
        parser = FCVParser(filepath, verbose=verbose, endianness=endianness)
        # Parse the file (header, nodes, keyframes, etc.)
        parser.parse()

        # Retrieve summary info for display
        info = parser.get_summary()

        # Optionally export parsed data to JSON
        if export_json:
            parsed_data = parser.to_dict()
            json_path = os.path.splitext(filepath)[0] + ".json"
            with open(json_path, "w", encoding="utf-8") as jf:
                json.dump(parsed_data, jf, indent=2)
            print(f"[JSON] Parsed data exported to: {json_path}")

        # Print summary information to terminal
        print(f"=== FCV File Summary ===")
        print(f"Max Time    : {info['max_time']} frames")
        print(f"Node Count  : {info['node_count']}")
        print(f"File Size   : {info['file_size']} bytes")
        print(f"File Size_F : {info['real_file_size']} bytes")
        print(f"Padding     : {info['padding']} byte(s)")
        print(Fore.GREEN + ".FCV parsing complete. See debug .log file for details.\n" + Style.RESET_ALL)
        return None
        
    except struct.error as e:
     # Handle parsing error due to struct unpacking (likely endian mismatch)
        current_offset = hex(getattr(parser, "_file_offset", 0))
        msg = f"{e} at file offset: {current_offset}\nThis might be caused by incorrect endian mode.\nPossible Improper Endianess in header! \nTry running with the other endian: 'little' ↔ 'big'"
        return msg
    except Exception as e:
        # Handle all other exceptions (return the error message)
        return str(e)

def main():
    """
    Main entry point for the FCV processing script.
    Handles command-line arguments, processes files, and reports errors.
    """
    export_json = False
    error_files = []

    # Check if user provided at least one argument
    if len(sys.argv) < 2:
        print("Usage: python run_fcv.py <file_or_folder_path> [-little|-big] [-json] [-verbose] ")
        print("If no endian is specified, it will try to detect the endian. ")
        return

    path = sys.argv[1]  # First argument is the file or folder path
    endian_arg = None   # Optional override for file endianness ('<' or '>')
    verbose = False     # Verbose flag for dumping log to terminal

    for arg in sys.argv[2:]:
        if arg.lower() in ["-little", "-big"]:
            endian_arg = "<" if arg.lower() == "little" else ">"
        elif arg.lower() == "-json":
            export_json = True  # Enable JSON export
        elif arg.lower() == "-verbose":
            verbose = True

    if os.path.isfile(path) and path.lower().endswith(".fcv"):
        err = process_file(path, verbose, force_endian=endian_arg, export_json=export_json)
        if err:
            error_files.append((path, err))
    elif os.path.isdir(path):
        for fname in os.listdir(path):
            if fname.lower().endswith(".fcv"):
                full_path = os.path.join(path, fname)
                err = process_file(full_path, verbose, force_endian=endian_arg, export_json=export_json)
                if err:
                    error_files.append((full_path, err))
    else:
        print("Invalid path or no .FCV files found.")

    # Print error report if any files failed to parse
    if error_files:
        print("\n" + Fore.RED + "=== FCV FILES FAILED TO PARSE ===" + Style.RESET_ALL)
        for f, msg in error_files:
            print(Fore.RED + f"[ERROR] {f}" + Style.RESET_ALL + f": {msg}")

if __name__ == "__main__":
    main()
