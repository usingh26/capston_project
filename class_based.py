import json
import csv
from pathlib import Path
import sys
import re


class Validator:
    """Base class for all validators"""
    validator_count = 0

    def __init__(self, field_name):
        self.field_name = field_name
        Validator.validator_count += 1

    def validate(self, data):
        """validator must implement this method"""
        raise NotImplementedError("Every validator must implement validate()")

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.field_name!r})"

    def __eq__(self, value):
        if not isinstance(value, Validator):
            return NotImplemented
        return (self.__class__ == value.__class__
                and self.field_name == value.field_name)

    @staticmethod
    def is_positive(val):
        try:
            return float(val)>0
        except(ValueError,TypeError):
            return False

    @classmethod
    def get_validator_count(cls):
        """Return number of validator created"""
        return cls.validator_count


class FilenameValidator(Validator):
    def __init__(self):
        super().__init__("filename")

    def validate(self, data):
        filename = data.get("filename", "").strip()
            
        if not filename or not filename.lower().endswith(".pdf"):
            return "INVALID_FILENAME"
        
        return None

class ModuleCodeValidator(Validator):
    def __init__(self):
        super().__init__("module_code")

    def validate(self, data):
        module_code = data.get("module_code","").strip()
            
        if not re.fullmatch(r"[A-Z]{2,4}-\d{3}",module_code):
            return "INVALID_MODULE_CODE"

        return None

class PageCountValidator(Validator):
    def __init__(self):
        super().__init__("page_count")

    def validate(self, data):
        try:
            page_count = int(data.get("page_count", ""))
    
            if page_count <= 0:
                return "INVALID_PAGE_COUNT"
        except (ValueError, TypeError):
            return "INVALID_PAGE_COUNT"

        return None

class FileSizeValidator(Validator):
    def __init__(self):
        super().__init__("file_size_kb")

    def validate(self, data):
        try:
            file_size = float(data.get("file_size_kb", ""))
            if file_size <= 0:
                return "INVALID_FILE_SIZE"
        except (ValueError, TypeError):
            return "INVALID_FILE_SIZE"

        return None

class BooleanFieldValidator(Validator):
    def __init__(self, field_name):
        super().__init__(field_name)

    def validate(self, data):
        val = str(data.get(self.field_name, "")).strip().lower()

        if val not in ("true", "false"):
            return "INVALID_"+ self.field_name.upper()

        return None

class StatusValidator(Validator):
    def __init__(self, allowed_statuses):
        super().__init__("status")

        self.allowed_statuses = {status.lower() for status in allowed_statuses}

    def validate(self, data):
        status = str(data.get("status") or "").strip().lower()

        if status not in self.allowed_statuses:
            return "INVALID_STATUS"

        return None
        








class MissingManifestError(Exception):
    pass
class InvalidRowError(Exception):
    pass



class PdfModuleComplianceAuditor:


    def __init__(self, allowed_statuses=None):
        if allowed_statuses is None:
            allowed_statuses = {"draft","review","final"}

        self.allowed_statuses = { status.lower() for status in allowed_statuses}

        self.validators = [FilenameValidator(),ModuleCodeValidator(),PageCountValidator(),
                           FileSizeValidator(),BooleanFieldValidator("has_toc"),
                           BooleanFieldValidator("has_images"), StatusValidator(self.allowed_statuses)]

        
    def read_file(self, file_path):
        try:
            if file_path.suffix.lower() == ".csv":
                with open(file_path, "r", newline="", encoding="utf-8") as file:
                    reader = csv.DictReader(file)
                    # return list(reader)
        
                    for row in reader:
                        yield row
                    
            elif file_path.suffix.lower()==".json":
                with open(file_path, "r", encoding="utf-8") as file:
                    records = json.load(file)
        
                if not isinstance(records, list):
                    raise ValueError("Json file must have a list of records")
        
                # return records
                for record in records:
                    yield record
        
            else:
                    raise ValueError("Unsupported file type")

        except FileNotFoundError as error:
             raise MissingManifestError(f"Manifest file not found: {file_path}") from error
             
        
        


        
        
    def validate_data(self, data):
        issues = []

        for validator in self.validators:
            issue = validator.validate(data)

            if issue is not None:
                issues.append(issue)

        return issues

    
    def create_report(self, lines):
        lines = list(lines)
        validated_data = list(map(self.validate_data, lines))
    
        results = list(zip(lines, validated_data))
    
        total_files = len(lines)
        compliant_records = list(filter(lambda result: len(result[1])==0, results))
    
        compliant_count = len(compliant_records)
        non_compliant_count = len(results)-len(compliant_records)
    
        if len(results) > 0:
            compliance_rate = round(len(compliant_records)/len(results) * 100,2)
    
        else:
            compliance_rate = 0.0
    
        issues_by_file = {
            str(result[0].get("filename") or ""): result[1]
            for result in results
        }
    
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
    
        summary_by_module = {
            module_code: round(counts["compliant"]/counts["total"]*100,2)
            for module_code, counts in module_counts.items()
        }
    
        report = {
            "total_files": total_files,
            "compliant_count": compliant_count,
            "non_compliant_count": non_compliant_count,
            "compliance_rate": compliance_rate,
            "issues_by_file": issues_by_file,
            "summary_by_module": summary_by_module
        }
        return report




if __name__ == "__main__":
    auditor = PdfModuleComplianceAuditor()

    current_folder = Path(__file__).resolve().parent
    root_folder = current_folder.parent
    input_path = root_folder / "sample_data" / "sample_manifest.csv"

    try:
        lines = auditor.read_file(input_path)
        report = auditor.create_report(lines)

        op_folder = root_folder / "compliance_report"
        op_folder.mkdir(parents=True, exist_ok=True)

        op_path = op_folder / "compliance_report.json"

        with open(op_path, "w", encoding="utf-8") as file:
            json.dump(report, file, indent=4)

    except (
        MissingManifestError,
        InvalidRowError,
        OSError,
        ValueError,
        csv.Error,
        json.JSONDecodeError
    ) as error:
        print(f"Error: {error}", file=sys.stderr)

    else:
        print(f"Report saved to: {op_path}")

    finally:
        print("Auditor execution finished.", file=sys.stderr)