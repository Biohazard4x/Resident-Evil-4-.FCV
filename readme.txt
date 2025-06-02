
Resident Evil 4 FCV Python Parser 
================================================

The colorama module must be installed for use(pip install colorama)

The FCV.fcv_parser module (included or must be present in the same folder or FCV/ subdirectory)


"run_FCV.exe <file_or_folder_path> [options]"

-little	  -Force Little Endian parsing (default is auto-detect)
-big	 - Force Big Endian parsing
-json	 - Export parsed output as a .json file (same base name as .fcv)
-verbose - Show debug/log output in the terminal


Parse a single FCV file (auto-endian detect): run_FCV.exe motion.fcv

Batch-parse all .fcv files in a folder, :run_FCV.exe FCV_files_folder


================================================
License & Credits
Resident Evil 4 and related assets are © Capcom. This tool is for educational and modding purposes only.
Use at your own risk.