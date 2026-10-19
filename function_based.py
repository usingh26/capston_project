import csv
import json
import re
from pathlib import Path

# reading csv/json file 
def read_file(file_path):
    if file_path.suffix.lower() == ".csv":
        with open(file_path, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            return list(reader)

    elif file_path.suffix.lower()==".json":
        with open(file_path, "r", encoding="utf-8") as file:
            records = json.load(file)

        if not isinstance(records, list):
            raise ValueError("Json file must have a list of records")

        return records

    else:
        raise ValueError("Unsupported file type")


# validator function 
def validate_data(data):
    issues = []

# validating filename 
    filename = data.get("filename", "").strip()

    if not filename or not filename.lower().endswith(".pdf"):
        issues.append("INVALID_FILENAME")

# validating module code 
    module_code = data.get("module_code","").strip()

    if not re.fullmatch(r"[A-Z]{2,4}-\d{3}",module_code):
        issues.append("INVALID_MODULE_CODE")    

# validating page count 
    try:
        page_count = int(data.get("page_count", ""))

        if page_count <= 0:
            issues.append("INVALID_PAGE_COUNT")
    except (ValueError, TypeError):
        issues.append("INVALID_PAGE_COUNT")

# validating file size 
    try:
        file_size = float(data.get("file_size_kb", ""))
        if file_size <= 0:
            issues.append("INVALID_FILE_SIZE")
    except (ValueError, TypeError):
        issues.append("INVALID_FILE_SIZE")

# validating boolean strings 

    fields = ["has_toc", "has_images"]

    for field in fields:
        value = str(data.get(field, ""))
        value = value.strip().lower()
    
        if value != "true" and value != "false":
            issue_code = "INVALID_" + field.upper()
            issues.append(issue_code)

# vakidating status 
    valid_status = {"draft", "review", "final"}
    status = data.get("status", "").strip().lower()

    if status not in valid_status:
        issues.append("INVALID_STATUS")

    return issues


# creating report
def create_report(lines):
    validated_data = list(map(validate_data, lines))

    results = list(zip(lines, validated_data))

    total_files = len(lines)
    compliant_records = []
    for result in results:
        issue = result[1]

        if len(issue) == 0:
            compliant_records.append(result)

    compliant_count = len(compliant_records)
    non_compliant_count = len(results)-len(compliant_records)

    if len(results) > 0:
        compliance_rate = round(len(compliant_records)/len(results) * 100,2)

    else:
        compliance_rate = 0.0

    issues_by_file = {}

    for result in results:
        data = result[0]
        issue = result[1]

        filename = str(data.get("filename") or "")
        issues_by_file[filename] = issue

    module_counts = {}

    for result in results:
        data = result[0]
        module_code = str(data.get("module_code") or "")
        issue = result[1]

        if module_code not in module_counts:
            module_counts[module_code] = {
                "total": 0,
                "compliant": 0
            }

        module_counts[module_code]["total"] += 1

        if len(issue) == 0:
            module_counts[module_code]["compliant"] += 1

    summary_by_module = {}

    for module_code in module_counts:
        total = module_counts[module_code]["total"]
        compliant = module_counts[module_code]["compliant"]

        rate = round(compliant / total * 100, 2)
        summary_by_module[module_code] = rate

    report = {
        "total_files": total_files,
        "compliant_count": compliant_count,
        "non_compliant_count": non_compliant_count,
        "compliance_rate": compliance_rate,
        "issues_by_file": issues_by_file,
        "summary_by_module": summary_by_module
    }
    return report

        



# main
current_folder = Path(__file__).resolve().parent

root_folder = current_folder.parent

input_path = root_folder/"sample_data"/"sample_manifest.csv"

try:
    lines = read_file(input_path)
    report = create_report(lines)
    op_folder = root_folder/"compliance_report"

    op_folder.mkdir(parents=True, exist_ok=True)

    op_path = op_folder/"compliance_report.json"

    with open(op_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print(f"Report saved to: {op_path}")

except (OSError, ValueError, csv.Error, json.JSONDecodeError) as error:
    print(f"Error: {error}")





