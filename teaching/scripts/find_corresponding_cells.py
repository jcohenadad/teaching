import csv

def read_csv(filename, column_number, delimiter):
    """
    Read a CSV file and return the data in the specified column as a list.
    """
    data = []
    with open(filename, 'r') as f:
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            if len(row) > column_number:
                data.append(row[column_number])
    return data

def find_non_correspondence(file1, column1, delimiter1, file2, column2, delimiter2):
    """
    Find lines that do not correspond between two CSV files based on the specified columns.
    """
    data1 = read_csv(file1, column1, delimiter1)
    data2 = read_csv(file2, column2, delimiter2)

    non_correspondence1 = []
    non_correspondence2 = []

    for i, val1 in enumerate(data1):
        if val1 not in data2:
            non_correspondence1.append(i)

    for j, val2 in enumerate(data2):
        if val2 not in data1:
            non_correspondence2.append(j)

    return non_correspondence1, non_correspondence2

def main():
    # Take inputs from the user
    file1 = 'src1.CSV'  #input("Enter the name of the first CSV file: ")
    column1 = 0  #int(input(f"Enter the column number to match in {file1}: "))
    delimiter1 = ';'  #input(f"Enter the delimiter for {file1} (e.g., ',' or ';'): ")
    
    file2 = 'dest.csv'  #input("Enter the name of the second CSV file: ")
    column2 = 1  #int(input(f"Enter the column number to match in {file2}: "))
    delimiter2 = ','  #input(f"Enter the delimiter for {file2} (e.g., ',' or ';'): ")

    # Find non-corresponding lines
    non_correspondence1, non_correspondence2 = find_non_correspondence(file1, column1, delimiter1, file2, column2, delimiter2)

    # Print the results
    if non_correspondence1 or non_correspondence2:
        print("Lines that do not have corresponding matches:")
        for i in non_correspondence1:
            print(f"Line {i+1} in {file1} does not have a corresponding match in {file2}.")
        for j in non_correspondence2:
            print(f"Line {j+1} in {file2} does not have a corresponding match in {file1}.")
    else:
        print("All lines have corresponding matches between the two files.")

if __name__ == '__main__':
    main()
