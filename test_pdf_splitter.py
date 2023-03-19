import unittest
import pdf_splitter

test_toc = [
    {"level": 1, "name": "Copyright", "page": 1},
    {"level": 1, "name": "Table of Contents", "page": 2},
    {"level": 1, "name": "Part I: Basics", "page": 3},
    {"level": 2, "name": "Chapter 1", "page": 4},
    {"level": 2, "name": "Chapter 2", "page": 5},
    {"level": 2, "name": "Chapter 3", "page": 6},
    {"level": 3, "name": "Chapter 3.1", "page": 7},
    {"level": 4, "name": "Chapter 3.1.1", "page": 8},
    {"level": 2, "name": "Chapter 4", "page": 9},
    {"level": 2, "name": "Chapter 5", "page": 10},
    {"level": 1, "name": "Part II: Advanced", "page": 11},
    {"level": 2, "name": "Chapter 6", "page": 12},
    {"level": 2, "name": "Chapter 7", "page": 13},
    {"level": 1, "name": "Appendix A", "page": 14},
    {"level": 1, "name": "Index", "page": 15},
]


class TestPdfSplitter(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_n_levels(self):
        result_1 = pdf_splitter.get_n_levels(test_toc, 2)
        self.assertEqual(len(result_1), 13)

        result_2 = pdf_splitter.get_n_levels(test_toc, 1)
        self.assertEqual(len(result_2), 6)

        result_3 = pdf_splitter.get_n_levels(test_toc, 10)
        self.assertEqual(len(result_3), len(test_toc))

    def test_get_page_ranges(self):
        page_count = len(test_toc)

        page_ranges_1 = pdf_splitter.get_page_ranges(
            test_toc, 1, False, page_count)
        self.assertEqual(page_ranges_1[0]["name"], "Copyright")
        self.assertEqual(page_ranges_1[1]["page_range"][0], 2)
        self.assertEqual(page_ranges_1[1]["page_range"][1], 2)

        # Nested sections are extracted correctly
        self.assertEqual(page_ranges_1[2]["name"], "Part I: Basics")
        self.assertEqual(page_ranges_1[2]["page_range"][0], 3)
        self.assertEqual(page_ranges_1[2]["page_range"][1], 10)

        self.assertEqual(page_ranges_1[3]["name"], "Part II: Advanced")
        self.assertEqual(page_ranges_1[3]["page_range"][0], 11)
        self.assertEqual(page_ranges_1[3]["page_range"][1], 13)

        # Last page is inserted correctly
        self.assertEqual(page_ranges_1[5]["page_range"][1], page_count - 1)

        self.assertEqual(len(page_ranges_1), 6)

        page_ranges_2 = pdf_splitter.get_page_ranges(
            test_toc, 2, False, page_count)
        self.assertEqual(page_ranges_2[2]["name"], "Chapter 3")
        self.assertEqual(page_ranges_2[2]["page_range"][0], 6)
        self.assertEqual(page_ranges_2[2]["page_range"][1], 8)

        self.assertEqual(page_ranges_2[6]["name"], "Chapter 7")
        self.assertEqual(page_ranges_2[6]["page_range"][0], 13)
        self.assertEqual(page_ranges_2[6]["page_range"][1], 13)

        self.assertEqual(len(page_ranges_2), 7)

        # Overlapping works
        page_ranges_3 = pdf_splitter.get_page_ranges(
            test_toc, 2, True, page_count)
        self.assertEqual(page_ranges_3[2]["name"], "Chapter 3")
        self.assertEqual(page_ranges_3[2]["page_range"][0], 6)
        self.assertEqual(page_ranges_3[2]["page_range"][1], 9)

        self.assertEqual(page_ranges_3[6]["name"], "Chapter 7")
        self.assertEqual(page_ranges_3[6]["page_range"][0], 13)
        self.assertEqual(page_ranges_3[6]["page_range"][1], 14)

        self.assertEqual(len(page_ranges_3), 7)

    def test_unnamed_toc(self):
        unnamed_test_toc = [
            {"level": 1, "name": "", "page": 1},
            {"level": 1, "name": "", "page": 2},
            {"level": 1, "name": "", "page": 3},
            {"level": 2, "name": "", "page": 4},
            {"level": 2, "name": "", "page": 5},
            {"level": 2, "name": "", "page": 6},
            {"level": 3, "name": "", "page": 7},
            {"level": 4, "name": "", "page": 8},
            {"level": 2, "name": "", "page": 9},
            {"level": 2, "name": "", "page": 10},
            {"level": 1, "name": "", "page": 11},
            {"level": 2, "name": "", "page": 12},
            {"level": 2, "name": "", "page": 13},
            {"level": 1, "name": "", "page": 14},
            {"level": 1, "name": "", "page": 15},
        ]

        page_count = len(unnamed_test_toc)

        page_ranges = pdf_splitter.get_page_ranges(
            unnamed_test_toc, 1, False, page_count)
        self.assertEqual(page_ranges[0]["name"], "Untitled Section")
        self.assertEqual(page_ranges[1]["name"], "Untitled Section 2")
        self.assertEqual(page_ranges[2]["name"], "Untitled Section 3")
        self.assertEqual(page_ranges[3]["name"], "Untitled Section 4")
        self.assertEqual(page_ranges[4]["name"], "Untitled Section 5")
        self.assertEqual(page_ranges[5]["name"], "Untitled Section 6")

    def test_filter_by_regex(self):
        page_count = len(test_toc)

        page_ranges_1 = pdf_splitter.get_page_ranges(
            test_toc, 1, False, page_count)
        self.assertEqual(len(page_ranges_1), 6)

        filtered_1 = pdf_splitter.filter_by_regex(page_ranges_1, "^Part")
        self.assertEqual(len(filtered_1), 2)

        page_ranges_2 = pdf_splitter.get_page_ranges(
            test_toc, 2, False, page_count)
        self.assertEqual(len(page_ranges_2), 7)

        filtered_2 = pdf_splitter.filter_by_regex(
            page_ranges_2, "^Chapter [123]")
        self.assertEqual(len(filtered_2), 3)

    def test_safe_filename(self):
        self.assertEqual(pdf_splitter.safe_filename(
            "file!@#$*'?`файл"), "fileфайл")


if __name__ == "__main__":
    unittest.main()
