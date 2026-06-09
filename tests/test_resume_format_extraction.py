import unittest
from pathlib import Path

from backend.parsers.docx_reader import read_docx
from backend.parsers.section_splitter import split_sections
from backend.parsers.extractors.academic_role import AcademicRoleExtractor
from backend.parsers.extractors.award import AwardExtractor
from backend.parsers.extractors.paper import PaperExtractor
from backend.parsers.extractors.patent import PatentExtractor
from backend.parsers.extractors.software_copyright import SoftwareCopyrightExtractor
from backend.parsers.extractors.special_issue import SpecialIssueExtractor


class UnifiedResumeFormatExtractionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        docx_path = next(Path(".").glob("*格式统一版*.docx"))
        cls.sections = split_sections(**_read_docx_sections(docx_path))

    def test_template_sections_are_split_without_body_truncation(self):
        self.assertEqual(242, len(self.sections["paper"]))
        self.assertEqual(54, len(self.sections["project"]))
        self.assertEqual(16, len(self.sections["software_copyright"]))
        self.assertEqual(20, len(self.sections["academic_role"]))
        self.assertTrue(self.sections["software_copyright"][0].endswith("软件著作权登记号：2014SR135294。"))

    def test_papers_extract_all_template_lines_and_key_metadata(self):
        papers = PaperExtractor().extract(self.sections["paper"])
        self.assertEqual(len(self.sections["paper"]), len(papers))

        flds = _find_item(papers, "FLDS: An Intelligent Feature Learning Detection System")
        self.assertEqual("IEEE Journal of Biomedical and Health Informatics", flds["journal"])
        self.assertEqual("4814-4825", flds["pages"])
        self.assertTrue(any(author["name"] == "Shanchen Pang" and author["is_corresponding_author"]
                            for author in flds["authors"]))

        lithology = _find_item(papers, "Lithology identification from missing well log data")
        self.assertEqual("Advanced Engineering Informatics", lithology["journal"])
        self.assertEqual("10.1016/j.aei.2026.104697", lithology["doi"])
        self.assertEqual("一区", lithology["cas_partition"])
        self.assertNotEqual("EI", lithology.get("source_type"))

    def test_software_patent_award_and_issue_fields_follow_template(self):
        software = SoftwareCopyrightExtractor().extract(self.sections["software_copyright"])
        self.assertEqual("庞善臣，赵慧奇，徐誉尹，李源桦，杨杰，王春", software[0]["applicant"])
        self.assertEqual("基于虚拟机的电子商务安全控制软件（V1.0）", software[0]["name"])
        self.assertEqual("2014SR135294", software[0]["registration_number"])

        patents = PatentExtractor().extract(self.sections["patent"])
        last_patent = patents[-1]
        self.assertEqual("CN202511916732.X", last_patent["application_number"])
        self.assertEqual("", last_patent["authorization_number"])
        self.assertEqual("公开", last_patent["status"])

        awards = AwardExtractor().extract(self.sections["award"])
        self.assertEqual("中国电子学会", awards[0]["awarding_body"])
        self.assertEqual("山东高等学校优秀科研成果", awards[-1]["awarding_body"])

        issues = SpecialIssueExtractor().extract(self.sections["special_issue"])
        self.assertEqual("Sensors", issues[0]["journal_name"])

    def test_academic_roles_are_one_item_per_template_line(self):
        roles = AcademicRoleExtractor().extract(self.sections["academic_role"])
        self.assertEqual(20, len(roles))
        self.assertEqual("《AI & Materials》期刊副主编", roles[-1]["title"])
        self.assertEqual("2024年6月1日", roles[-1]["start_date"])
        self.assertEqual("2026年5月31日", roles[-1]["end_date"])


def _read_docx_sections(path: Path):
    data = read_docx(str(path))
    return {"paragraphs": data["paragraphs"], "tables": data["tables"]}


def _find_item(items, title_part):
    for item in items:
        if title_part in item.get("title", ""):
            return item
    raise AssertionError(f"Item containing {title_part!r} was not found")


if __name__ == "__main__":
    unittest.main()
