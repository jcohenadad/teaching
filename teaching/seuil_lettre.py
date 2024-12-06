# Author: Robin Demesmaeker

import argparse

def parse_thresholds(threshold_list):
    """
    Parse thresholds in the form "LABEL:PERCENTILE" from the command line.
    Returns a list of (label, percentile) tuples sorted by percentile descending.
    """
    thresholds = []
    for item in threshold_list:
        label, val_str = item.split(":")
        val = float(val_str)
        thresholds.append((label, val))
    # Sort by percentile in descending order (so the highest percentile is first)
    thresholds.sort(key=lambda x: x[1], reverse=True)
    return thresholds

def percentile_grade(sorted_grades, percentile):
    """
    Return the grade at the given percentile.
    Percentile should be between 0 and 1.
    If percentile = 0.9, we want the 90th percentile.
    """
    if not sorted_grades:
        return None
    n = len(sorted_grades)
    # Using nearest-rank method:
    # rank = ceil(p * n), but we can also use linear interpolation.
    # For simplicity, use an index-based approach:
    # index for percentile p = (p * (n - 1))
    idx = int(round(percentile * (n - 1)))
    return sorted_grades[idx]

def main():
    parser = argparse.ArgumentParser(description="Compute letter grade thresholds based on percentile ranks.")
    parser.add_argument("file_grades", type=str, help="Path to the file containing grades.")
    parser.add_argument("--max-grade", type=float, default=20.0, help="Maximum possible grade.")
    parser.add_argument("--thresholds", nargs="+", 
                        default=["A*:0.9","A:0.7","B+:0.5","B:0.3","C+:0.2","C:0.1","D+:0.05","F:0.01"],
                        help='List of threshold definitions in the format "LABEL:PERCENTILE". '
                             'Example: "A*:0.9" "A:0.7" etc.')
    args = parser.parse_args()

    # Parse thresholds
    thresholds = parse_thresholds(args.thresholds)
    
    # Read grades
    with open(args.file_grades, 'r') as f:
        grades = [float(line.strip()) for line in f if line.strip()]

    # Sort grades
    grades.sort()

    # Compute and print thresholds
    print("Letter Grade Thresholds:")
    for label, p in thresholds:
        grade_cutoff = percentile_grade(grades, p)
        if grade_cutoff is None:
            print(f"{label}: No data available")
            continue
        # Convert grade cutoff to percentage of max grade
        percentage_of_max = (grade_cutoff / args.max_grade) * 100.0
        print(f"{label}: {grade_cutoff:.2f} (raw), {percentage_of_max:.2f}% of max")

if __name__ == "__main__":
    main()
