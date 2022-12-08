#!/usr/bin/env python
"""
This script finds the value of a source EXCEL file and insert it in a destination EXCEL file. The matching is done on
 a column specified in this script (eg: the 'matricule' of a student). The file should be edited to customize it.
"""

import sys
import openpyxl as xl
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")

# opening the source excel file
filename = "/Users/julien/Desktop/src.xlsx"
# WARNING!!! Starts at 1
col_id_src = 3
col_val_src = 9
row_start_src = 1
wb1 = xl.load_workbook(filename, read_only=True)
ws1 = wb1.active

# opening the destination excel file
filename1 = "/Users/julien/Desktop/dest.xlsx"
wb2 = xl.load_workbook(filename1)
ws2 = wb2.active
col_id_dest = 1
col_val_dest = 4
# row_start_dest = 11

file_out = "/Users/julien/Desktop/dest_modif.xlsx"

# Loop across rows from the src file
# This is a workaround found in https://localcoder.org/openpyxl-max-row-and-max-column-wrongly-reports-a-larger-figure
#  to address the problem of ws1.max_row outputting 'None' sometimes.
for n_row_src, row in enumerate(ws1, 1):
    if all(c.value is None for c in row):
        break


def invalid_cell(value):
    """
    Check if the cell value fits desired properties
    :param value:
    :return: False if the cell is OK, True otherwise.
    """
    if value is None:
        return True
    # Matricule should be a number
    if not value.isdigit():
        return True
    # Matricule should have 7 digits
    if not len(value) == 7:
        return True
    return False


# copying the cell values from source
# excel file to destination excel file
for i in range(row_start_src + 1, n_row_src + 1):
    # Read index value from source file
    id = ws1.cell(row=i, column=col_id_src).value
    # run some checks to make sure this index corresponds to the desired field
    if invalid_cell(id):
        continue
    # Read value from source file
    val = ws1.cell(row=i, column=col_val_src).value
    # Find index from dest file
    found = False
    for i_row in range(1, ws2.max_row + 1):
        for i_col in range(1, ws2.max_column + 1):
            cell = ws2.cell(i_row, i_col).value
            logger.debug(f"id: {id} | Cell ({i_row}, {i_col}): {cell}")
            if cell == id:
                found = True
                # Assign value in destination cell
                ws2.cell(i_row, col_val_dest).value = val
                break
    if not found:
        logger.error("Not found :-(")

# saving the destination excel file
wb2.save(file_out)

logger.info("Job done! 🎉")
