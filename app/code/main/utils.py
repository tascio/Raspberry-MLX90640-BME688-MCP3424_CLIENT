from main.models import csv_path, Threshold
import os, glob

def open_latest_csv():
    csv_files = glob.glob(os.path.join(csv_path, "*.csv"))
    if not csv_files:
        return False

    latest_file = max(csv_files, key=os.path.getmtime)
    return latest_file

def check_threshold(val, th):
    if (val - Threshold.air_temp) > th:
        return True
    else:
        return False