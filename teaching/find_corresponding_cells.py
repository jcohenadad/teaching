# Find non-corresponding lines between two CSV files based on specified columns
# Author: Julien Cohen-Adad

import csv
import argparse
from typing import List, Tuple

def read_csv(filename: str, column_number: int, delimiter: str) -> List[str]:
    """
    Read a CSV file and return the data in the specified column as a list.
    """
    data = []
    try:
        # Specify the encoding to handle non-UTF-8 encoded files
        with open(filename, mode='r', encoding='ISO-8859-1') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) > column_number:
                    data.append(row[column_number])
    except UnicodeDecodeError:
        print("UnicodeDecodeError: Unable to decode the file. Please check the file encoding.")
    return data


def find_non_correspondence(file1: str, column1: int, delimiter1: str, file2: str, column2: int, delimiter2: str) -> Tuple[List[int], List[int]]:
    """
    Find lines that do not correspond between two CSV files based on the specified columns.
    """
    data1 = read_csv(file1, column1, delimiter1)
    data2 = read_csv(file2, column2, delimiter2)

    non_correspondence1 = []
    non_correspondence2 = []

    for i, val1 in enumerate(data1):
        if val1 not in data2:
            non_correspondence1.append(i + 1)  # Line numbers start from 1

    for j, val2 in enumerate(data2):
        if val2 not in data1:
            non_correspondence2.append(j + 1)  # Line numbers start from 1

    return non_correspondence1, non_correspondence2

def main():
    parser = argparse.ArgumentParser(description="Find non-corresponding lines between two CSV files based on specified columns. This script is useful to see new students in an updated list of students.")
    
    parser.add_argument("file1", help="Name of the first CSV file")
    parser.add_argument("--column1", type=int, default=0, help="Column number to match in the first file (default is 0)")
    parser.add_argument("--delimiter1", default=";", help="Delimiter for the first file (default is ';')")
    
    parser.add_argument("file2", help="Name of the second CSV file")
    parser.add_argument("--column2", type=int, default=0, help="Column number to match in the second file (default is 0)")
    parser.add_argument("--delimiter2", default=";", help="Delimiter for the second file (default is ';')")
    
    args = parser.parse_args()
    
    non_correspondence1, non_correspondence2 = find_non_correspondence(args.file1, args.column1, args.delimiter1, args.file2, args.column2, args.delimiter2)
    
    print(f"Lines in {args.file1} that do not have a corresponding match in {args.file2}: {non_correspondence1}")
    print(f"Lines in {args.file2} that do not have a corresponding match in {args.file1}: {non_correspondence2}")

if __name__ == '__main__':
    main()
