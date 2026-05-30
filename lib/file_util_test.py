import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from lib.file_util import (
    Card,
    due_words_from_difficult_map,
    increment_daily_progress,
    load_daily_progress_total,
    merge_new_word_into_dictionary,
    parse_daily_progress_text,
    parse_dictionary_text,
    parse_difficult_text,
    parse_practice_list_text,
    serialize_daily_progress,
    serialize_practice_list,
)


class TestFileUtil(unittest.TestCase):
    def test_parse_dictionary_keeps_entries_without_sentence(self):
        text = "\n".join(
            [
                "a menudo",
                "hola : hello",
                "adios : goodbye :",
                "gato : cat : el gato duerme",
                "uno : : solo ejemplo",
            ]
        )

        cards = parse_dictionary_text(text)

        self.assertIn("a menudo", cards)
        self.assertEqual(cards["a menudo"].meaning, "")
        self.assertEqual(cards["a menudo"].example, "")
        self.assertIn("hola", cards)
        self.assertEqual(cards["hola"].meaning, "hello")
        self.assertEqual(cards["hola"].example, "")
        self.assertEqual(cards["adios"].example, "")
        self.assertEqual(cards["gato"].example, "el gato duerme")
        self.assertEqual(cards["uno"].meaning, "")
        self.assertEqual(cards["uno"].example, "solo ejemplo")

    def test_parse_dictionary_ignores_malformed_lines(self):
        text = "\n".join(
            [
                "# comment",
                "",
                " : missingword",
                "perro : dog :",
            ]
        )

        cards = parse_dictionary_text(text)

        self.assertEqual(set(cards.keys()), {"perro"})

    def test_parse_practice_and_serialize_dedup(self):
        text = "\n".join(["# c", "hola", "", "hola", "adios"])
        parsed = parse_practice_list_text(text)
        self.assertEqual(parsed, ["hola", "hola", "adios"])

        serialized = serialize_practice_list(parsed)
        self.assertEqual(serialized, "hola\nadios\n")

    def test_parse_difficult_keeps_latest_date_for_duplicates(self):
        text = "\n".join(
            [
                "2026-02-01,hola",
                "2026-02-03,hola",
                "2026-02-02,adios",
                "bad line",
            ]
        )

        parsed = parse_difficult_text(text)

        self.assertEqual(parsed["hola"], date(2026, 2, 3))
        self.assertEqual(parsed["adios"], date(2026, 2, 2))
        self.assertEqual(len(parsed), 2)

    def test_due_words_from_difficult_map(self):
        m = {
            "hola": date(2026, 2, 20),
            "adios": date(2026, 3, 1),
        }

        due = due_words_from_difficult_map(
            m,
            interval_days=7,
            today=date(2026, 3, 8),
        )

        self.assertEqual(set(due), {"hola", "adios"})

    def test_merge_new_word_into_dictionary_appends_meaning_and_examples(self):
        dictionary = {
            "hola": Card(word="hola", meaning="hello", example="hola amigo"),
        }
        new_card = Card(word="hola", meaning="hi", example="hola a todos")

        merged = merge_new_word_into_dictionary(new_card, dictionary)

        self.assertEqual(merged.word, "hola")
        self.assertEqual(merged.meaning, "hello, hi")
        self.assertIn("hola amigo", merged.example)
        self.assertIn("hola a todos", merged.example)

    def test_merge_new_word_empty_meaning_keeps_existing_meaning_and_merges_example(self):
        dictionary = {
            "hola": Card(word="hola", meaning="hello", example="hola amigo"),
        }
        new_card = Card(word="hola", meaning="", example="hola de nuevo")

        merged = merge_new_word_into_dictionary(new_card, dictionary)

        self.assertEqual(merged.meaning, "hello")
        self.assertIn("hola amigo", merged.example)
        self.assertIn("hola de nuevo", merged.example)

    def test_daily_progress_parse_and_serialize_recomputes_total(self):
        text = "date,new,review,day_5,day_15,today,total\n2026-05-29,1,2,3,4,5,999\n"

        rows = parse_daily_progress_text(text)
        self.assertEqual(rows["2026-05-29"]["total"], 15)

        serialized = serialize_daily_progress(rows)
        self.assertIn("2026-05-29,1,2,3,4,5,15", serialized)

    def test_increment_daily_progress_creates_and_updates_day_row(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "daily_progress.csv"

            increment_daily_progress(str(path), "new", day=date(2026, 5, 29))
            increment_daily_progress(str(path), "review", day=date(2026, 5, 29))
            increment_daily_progress(str(path), "new", day=date(2026, 5, 29))

            rows = parse_daily_progress_text(path.read_text(encoding="utf-8"))

        self.assertEqual(rows["2026-05-29"]["new"], 2)
        self.assertEqual(rows["2026-05-29"]["review"], 1)
        self.assertEqual(rows["2026-05-29"]["total"], 3)

    def test_load_daily_progress_total_returns_today_total(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "daily_progress.csv"
            path.write_text(
                "date,new,review,day_5,day_15,today,total\n"
                "2026-05-29,1,2,3,4,5,15\n",
                encoding="utf-8",
            )

            total = load_daily_progress_total(str(path), day=date(2026, 5, 29))
            missing_total = load_daily_progress_total(str(path), day=date(2026, 5, 30))

        self.assertEqual(total, 15)
        self.assertEqual(missing_total, 0)


if __name__ == "__main__":
    unittest.main()
