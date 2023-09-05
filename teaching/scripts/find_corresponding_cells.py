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

def find_correspondence(file1, column1, delimiter1, file2, column2, delimiter2):
    """
    Find the correspondance between two CSV files based on the specified columns.
    """
    data1 = read_csv(file1, column1, delimiter1)
    data2 = read_csv(file2, column2, delimiter2)

    correspondence = []

    for i, val1 in enumerate(data1):
        for j, val2 in enumerate(data2):
            if val1 == val2:
                correspondence.append((i, j))

    return correspondence

def main():
    # Take inputs from the user
    # file1 = input("Enter the name of the first CSV file: ")
    # column1 = int(input(f"Enter the column number to match in {file1}: "))
    # file2 = input("Enter the name of the second CSV file: ")
    # column2 = int(input(f"Enter the column number to match in {file2}: "))
    file1 = 'src1.CSV'
    column1 = 0
    delimiter1 = ';'
    file2 = 'dest.csv'
    column2 = 1
    delimiter2 = ','


    # Find the correspondance
    correspondence = find_correspondence(file1, column1, delimiter1, file2, column2, delimiter2)

    # Print the results
    if correspondence:
        print("Corresponding lines between the two files:")
        for i, j in correspondence:
            print(f"Line {i+1} in {file1} corresponds to line {j+1} in {file2}.")
    else:
        print("No correspondence found between the two files.")

if __name__ == '__main__':
    main()
