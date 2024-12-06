# The script reads a text file that has a series of grades (in single column), between 0 and 20, 
# and that outputs the threshold for the letter grade, according to the following rule based
# on the percentile of grades, example:
# >=90%: A*
# >=70%: A
# >=50%: B+
# >=30%: B
# >=20%: C+
# >=10%: C
# >=5%: D+
# >=1%: F
# 
# These thresholds are parametrizable (eg: as input parameter in argparse).
# 
# The output of the script gives the threshold, in percentage of the grade between 0 and 100%. 
# For example, if the threshold to get an A* is 18.0, then the output threshold for A* would be 90%.
# 
# Author: Julien Cohen-Adad


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
                        default=["A*:0.9","A:0.6","B+:0.4","B:0.2","C+:0.1","C:0.05","D+:0.02","F:0.01"],
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

    # Compute thresholds
    threshold_data = []
    for label, p in thresholds:
        grade_cutoff = percentile_grade(grades, p)
        count_at_or_above = sum(1 for g in grades if grade_cutoff is not None and g >= grade_cutoff)
        threshold_data.append((label, grade_cutoff, count_at_or_above))

    print("Letter Grade Thresholds:")
    previous_count = 0
    for (label, cutoff, count_current) in threshold_data:
        if cutoff is None:
            print(f"{label}: No data available")
            continue
        percentage_of_max = (cutoff / args.max_grade) * 100.0
        # Compute how many students are in this "band"
        count_in_category = count_current - previous_count
        print(f"{label}: {grade_cutoff:.2f} -> {percentage_of_max:.2f}% (n= {count_in_category})")
        previous_count = count_current

if __name__ == "__main__":
    main()
