"""
Phase 1 Structure Verification Tests

Verifies that all monorepo directories and essential configuration files exist.
"""

import unittest
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


class TestPhase1Structure(unittest.TestCase):

    def test_monorepo_directories_exist(self):
        required_directories = [
            "backend",
            "frontend",
            "data-generator",
            "ingestion",
            "kafka",
            "spark",
            "airflow",
            "dbt",
            "data-quality",
            "governance",
            "lineage",
            "contracts",
            "ml",
            "monitoring",
            "infrastructure",
            "tests",
            "docs",
            "scripts",
        ]
        for rel_path in required_directories:
            dir_path = BASE_DIR / rel_path
            self.assertTrue(dir_path.exists(), f"Directory missing: {rel_path}")
            self.assertTrue(dir_path.is_dir(), f"Not a directory: {rel_path}")

    def test_root_config_files_exist(self):
        required_files = [
            "README.md",
            ".gitignore",
            ".env.example",
            "Makefile",
            "LICENSE",
        ]
        for rel_path in required_files:
            file_path = BASE_DIR / rel_path
            self.assertTrue(file_path.exists(), f"File missing: {rel_path}")
            self.assertTrue(file_path.is_file(), f"Not a file: {rel_path}")

    def test_documentation_files_exist(self):
        doc_files = [
            "docs/requirements.md",
            "docs/architecture.md",
            "docs/data-flow.md",
            "docs/database.md",
        ]
        for rel_path in doc_files:
            file_path = BASE_DIR / rel_path
            self.assertTrue(file_path.exists(), f"Documentation missing: {rel_path}")


if __name__ == "__main__":
    unittest.main()

