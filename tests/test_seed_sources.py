from pathlib import Path
import unittest

from scripts import seed_sources


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "seed_sources.py"


class SeedSourcesTests(unittest.TestCase):
    def test_initial_sources_match_expected_metadata(self):
        sources = seed_sources.INITIAL_SOURCES

        self.assertEqual(len(sources), 10)
        self.assertEqual(
            [(source.source_type, source.title, source.language) for source in sources],
            [
                ("asme_2018_en", "ASME Y14.5-2018 English", "en"),
                ("asme_2009_es", "ASME Y14.5-2009 Español", "es"),
                ("aamc_course", "Módulo 0 Contenido del curso básico", "es"),
                ("aamc_course", "Módulo 1 Dimensionamiento y tolerancias", "es"),
                ("aamc_course", "Módulo 2 Definiciones dentro de las GD&T", "es"),
                ("aamc_course", "Módulo 3 Tolerancias de forma", "es"),
                (
                    "aamc_course",
                    "Módulo 4 Tolerancias de orientación y datum de referencia",
                    "es",
                ),
                ("aamc_course", "Módulo 5 Tolerancias de perfil", "es"),
                ("aamc_course", "Módulo 6 Tolerancias de localización", "es"),
                ("aamc_course", "Módulo 7 Tolerancia de cabeceo", "es"),
            ],
        )

    def test_seed_keys_are_unique_for_idempotency(self):
        keys = {
            (source.source_type, source.title, source.language, source.edition)
            for source in seed_sources.INITIAL_SOURCES
        }

        self.assertEqual(len(keys), len(seed_sources.INITIAL_SOURCES))
        self.assertIn("IS NOT DISTINCT FROM", seed_sources.SOURCE_EXISTS_SQL)

    def test_script_does_not_seed_definitions_or_questions(self):
        script = SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertIn("INSERT INTO sources", seed_sources.INSERT_SOURCE_SQL)
        self.assertNotIn("INSERT INTO definitions", script)
        self.assertNotIn("INSERT INTO course_question_patterns", script)
        self.assertNotIn("INSERT INTO adaptive_exercises", script)
        self.assertNotIn("postgresql://", script)
        self.assertNotIn("postgres://", script)


if __name__ == "__main__":
    unittest.main()
