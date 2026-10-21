from auditor.function_based import(read_file, validate_data, create_report, MissingManifestError, InvalidRowError)
import tempfile
import unittest
from pathlib import Path
import csv
import json

class TestValidateData(unittest.TestCase):
    """Test for validate_data function"""

    def setUp(self):
        self.valid_record = {
            "filename": "python.pdf",
            "module_code": "PY-101",
            "page_count": "25",
            "file_size_kb": "350.5",
            "has_toc": "true",
            "has_images": "true",
            "author": "Alice",
            "status": "final",
        }

    def test_valid_record(self):
        """Valid record should not have any issue"""

        issues = validate_data(self.valid_record)

        self.assertEqual(issues,[])

    def test_invalid_page_count(self):
        """A non numeric page count produce issue"""
        record = self.valid_record.copy()
        record["page_count"] = "abc"

        issues = validate_data(record)

        self.assertEqual(["INVALID_PAGE_COUNT"], issues)

    def test_zero_page_count(self):
        """Page count should be greater than zero"""
        record = self.valid_record.copy()
        record["page_count"] = "0"

        issues = validate_data(record)

        self.assertEqual(["INVALID_PAGE_COUNT"], issues)

    def test_edge_value(self):
        """Smallest positive page_count and file size"""

        record = self.valid_record.copy()
        record["page_count"] = "1"
        record["file_size_kb"] = "0.1"

        issues = validate_data(record)

        self.assertEqual(issues,[])

    def test_valid_status(self):
            """Status is valid only if it is allowed"""
            record = self.valid_record.copy()
            record["status"] = "draft"
    
            issues = validate_data(record)
    
            self.assertEqual(issues, [])

    def test_invalid_status(self):
        """Status is not allowed outside the allowed values"""
        record = self.valid_record.copy()
        record["status"] = "finished"

        issues = validate_data(record)

        self.assertEqual(issues, ["INVALID_STATUS"])

class TestReadFile(unittest.TestCase):
    """Test for reading csv or json file"""

    def test_read_csv(self):
        """CSV should be read as dictionary"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path =  Path(temp_dir) / "manifest.csv"
            with open(file_path, "w", newline="", encoding="utf-8") as file:
                 writer = csv.DictWriter(file, fieldnames=[
                     "filename",
                     "module_code",
                     "page_count",
                     "file_size_kb",
                     "has_toc",
                     "has_images",
                     "author",
                     "status",
                 ])
                 writer.writeheader()
                 writer.writerow({
                     "filename": "python.pdf",
                     "module_code": "PY-101",
                     "page_count": "25",
                     "file_size_kb": "350.5",
                     "has_toc": "true",
                     "has_images": "true",
                     "author": "Alice",
                     "status": "final",
                 })
            records = list(read_file(file_path))
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["filename"],"python.pdf")

    def test_read_json(self):
        """Json data should be read as dictionary"""
        with tempfile.TemporaryDirectory() as temp_dir:
                file_path = Path(temp_dir)/"manifest.json"
                expected_record = {
                     "filename": "python.pdf",
                      "module_code": "PY-101",
                      "page_count": "25",
                      "file_size_kb": "350.5",
                      "has_toc": "true",
                      "has_images": "true",
                      "author": "Alice",
                      "status": "final"
                }
                with open(file_path, "w", encoding="utf-8") as file:
                     json.dump([expected_record],file)
                
                records = list(read_file(file_path))
                
                self.assertEqual(records,[expected_record])

    def test_empty_csv(self):
        """A csv have header but no data should not return any record"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir)/"empty.csv"
            file_path.write_text("filename,module_code,page_count,file_size_kb,"
              "has_toc,has_images,author,status\n",
              encoding="utf-8",)
            
            records = list(read_file(file_path))
            self.assertEqual([],records)

    def test_missing_file(self):
         """Missing file should raise exception"""
         with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "missing.csv"

            with self.assertRaises(
                (MissingManifestError, FileNotFoundError)
            ):
                list(read_file(file_path))


class TestCreateReport(unittest.TestCase):
    """Tests for generating the comliance report"""
    def setUp(self):
          self.valid_record = {
               "filename": "python.pdf",
               "module_code": "PY-101",
               "page_count": "25",
               "file_size_kb": "350.5",
               "has_toc": "true",
               "has_images": "true",
               "author": "Alice",
               "status": "final",
          }

    def test_all_records_comliant(self):
        """All valid record should return 100% compliance rate"""
        records = [self.valid_record.copy(),
                   {
                        **self.valid_record,
                        "filename": "sql.pdf",
                        "module_code": "SQL-201",
                   }
        ]
        report = create_report(records)

        self.assertEqual(report["total_files"],2)
        self.assertEqual(report["compliant_count"], 2)
        self.assertEqual(report["non_compliant_count"], 0)
        self.assertEqual(report["compliance_rate"], 100.0)


    def test_single_record(self):
        """Create report should return correctly with one record"""
        report = create_report([self.valid_record.copy()])

        self.assertEqual(report["total_files"], 1)
        self.assertEqual(report["compliant_count"], 1)
        self.assertEqual(report["compliance_rate"], 100.0)

    def test_empty_input(self):
         """The empty input shoud have zero count and 0% rates"""
         report = create_report([])

         self.assertEqual(report["total_files"], 0)
         self.assertEqual(report["compliant_count"], 0)
         self.assertEqual(report["non_compliant_count"], 0)
         self.assertEqual(report["compliance_rate"], 0.0)
         self.assertEqual(report["issues_by_file"], {})
         self.assertEqual(report["summary_by_module"], {})


    def test_mix_compliance(self):
         """Valid and invalid record should counted correctly"""
         valid_record = self.valid_record.copy()
         invalid_record = self.valid_record.copy()
         invalid_record["filename"] = "notes.txt"
 
         report = create_report([valid_record, invalid_record])
 
         self.assertEqual(report["total_files"], 2)
         self.assertEqual(report["compliant_count"], 1)
         self.assertEqual(report["non_compliant_count"], 1)
         self.assertEqual(report["compliance_rate"], 50.0)
         self.assertIn("INVALID_FILENAME", report["issues_by_file"]["notes.txt"])

    def test_malformed_csv_row(self):
         """csv row missing colom should return InvalidRowError"""
         
    
         with tempfile.TemporaryDirectory() as temp_dir:
             file_path = Path(temp_dir) / "malformed.csv"
     
             file_path.write_text(
                 "filename,module_code,page_count,file_size_kb,"
                 "has_toc,has_images,author,status\n"
                 "python.pdf,PY-101,25\n",
                 encoding="utf-8",
             )
     
             with self.assertRaises(InvalidRowError):
                 list(read_file(file_path))