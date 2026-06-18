import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "lit_workflow.py"
spec = importlib.util.spec_from_file_location("lit_workflow", MODULE_PATH)
lit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lit)

class IndustryWorkflowTests(unittest.TestCase):
    def test_industry_args_are_registered(self):
        parser = lit.build_parser()
        args = parser.parse_args(["search", "--query", "anc", "--include-industry", "--industry-scope", "patents,products"])
        self.assertTrue(args.include_industry)
        self.assertEqual(args.industry_scope, "patents,products")

    def test_industry_scope_parser(self):
        self.assertEqual(lit.parse_industry_scope("patents, products,solutions"), {"patent", "product", "solution"})
        self.assertEqual(lit.parse_industry_scope("all"), {"patent", "product", "solution"})
        with self.assertRaises(SystemExit):
            lit.parse_industry_scope("patents,unknown")

    def test_load_industry_seed_has_required_benchmark_size(self):
        seed = Path(__file__).resolve().parents[1] / "seeds" / "industry_anc_benchmark_seed.json"
        records = lit.load_industry_seed(seed)
        products = [r for r in records if r["record_type"] == "product"]
        patents = [r for r in records if r["record_type"] == "patent"]
        solutions = [r for r in records if r["record_type"] == "solution"]
        self.assertGreaterEqual(len(products), 20)
        self.assertGreaterEqual(len(patents), 5)
        self.assertGreaterEqual(len(solutions), 5)
        for product in products:
            self.assertIn("curve_design", product)
            self.assertIn("source_url", product)

    def test_industry_records_are_normalized_with_evidence_grades(self):
        seed = Path(__file__).resolve().parents[1] / "seeds" / "industry_anc_benchmark_seed.json"
        records = lit.load_industry_seed(seed)
        allowed = {"official", "measurement", "review-derived", "inferred"}
        for record in records:
            self.assertIn(record["evidence_level"], allowed)
            self.assertTrue(record["evidence_basis"])
            self.assertTrue(record["source_url"])

        patents = [r for r in records if r["record_type"] == "patent"]
        measured_products = [r for r in records if r["record_type"] == "product" and "rtings.com" in r["source_url"]]
        self.assertTrue(all(r["evidence_level"] == "official" for r in patents))
        self.assertGreaterEqual(len([r for r in measured_products if r["evidence_level"] == "measurement"]), 15)

    def test_industry_outputs_include_evidence_in_jsonl_and_reports(self):
        seed = Path(__file__).resolve().parents[1] / "seeds" / "industry_anc_benchmark_seed.json"
        with tempfile.TemporaryDirectory() as tmp:
            old_industry = lit.INDUSTRY
            lit.INDUSTRY = Path(tmp)
            try:
                records = lit.load_industry_seed(seed)
                lit.write_industry_outputs(records, query="anc trust test", scope={"patent", "solution", "product"})
                jsonl = lit.INDUSTRY / "industry_records.jsonl"
                rows = [line for line in jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
                self.assertIn('"evidence_level":', rows[0])
                self.assertIn('"evidence_basis":', rows[0])

                patent_report = (lit.INDUSTRY / "patent_report.md").read_text(encoding="utf-8")
                solution_product_report = (lit.INDUSTRY / "solution_product_report.md").read_text(encoding="utf-8")
                integrated_report = (lit.INDUSTRY / "integrated_literature_industry_report.md").read_text(encoding="utf-8")
                for report in [patent_report, solution_product_report, integrated_report]:
                    self.assertIn("证据等级说明", report)
                    self.assertIn("evidence_level", report)
                    self.assertIn("evidence_basis", report)
            finally:
                lit.INDUSTRY = old_industry

    def test_industry_outputs_can_target_project_directory(self):
        seed = Path(__file__).resolve().parents[1] / "projects" / "anc" / "seeds" / "industry_benchmark_seed.json"
        records = lit.load_industry_seed(seed)
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "projects" / "sample-topic"
            lit.write_industry_outputs(
                records,
                query="project scoped industry test",
                scope={"patent", "solution", "product"},
                output_dir=lit.resolve_industry_output_dir(str(project_dir)),
                topic_label="Sample Topic ",
            )
            industry_dir = project_dir / "industry"
            self.assertTrue((industry_dir / "industry_records.jsonl").exists())
            integrated = (industry_dir / "integrated_literature_industry_report.md").read_text(encoding="utf-8")
            self.assertIn("文献与Sample Topic 信息整合报告", integrated)
            self.assertIn("evidence_level", integrated)

    def test_industry_reports_are_knowledge_reports_not_experiment_plans(self):
        report = Path(__file__).resolve().parents[1] / "industry" / "integrated_literature_industry_report.md"
        self.assertTrue(report.exists())
        text = report.read_text(encoding="utf-8")
        self.assertIn("知识库", text)
        self.assertNotIn("实验计划", text)
        self.assertNotIn("调参指令", text)

if __name__ == "__main__":
    unittest.main()
