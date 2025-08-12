# Traces Dataset

Each ZIP file contains one more CSV files with traces data. The CSV files have 502 columns, where the first two columns are 4 bytes sent and received from the microcontroller. The remaining 500 columns are the traces.

The file `data_summary.txt` contains the total number of traces and the number of traces corresponding to each Hamming Weight (0-32) in the entire dataset.