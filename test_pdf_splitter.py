import unittest
from collections import namedtuple
import pdf_splitter


class TestPdfSplitter(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_n_levels(self):
        test_toc = [
            [1, "Copyright", 1],
            [1, "Table of Contents", 2],
            [1, "Part I: Basics", 3],
            [2, "Chapter 1", 4],
            [2, "Chapter 2", 5],
            [2, "Chapter 3", 6],
            [3, "Section 3.1", 7],
            [4, "Section 3.1.1", 8],
            [2, "Chapter 4", 9],
            [2, "Chapter 5", 10],
            [1, "Part II: Advanced", 11],
            [2, "Chapter 6", 12],
            [2, "Chapter 7", 13],
            [1, "Appendix A", 14],
            [1, "Index", 15],
        ]

        result_1 = pdf_splitter.get_n_levels(test_toc, 2)
        self.assertEqual(len(result_1), 13)

        result_2 = pdf_splitter.get_n_levels(test_toc, 1)
        self.assertEqual(len(result_2), 6)

        result_3 = pdf_splitter.get_n_levels(test_toc, 10)
        self.assertEqual(len(result_3), len(test_toc))

    def test_get_page_ranges(self):
        test_toc = [
            [1, "Copyright", 1],
            [1, "Table of Contents", 2],
            [1, "Part I: Basics", 3],
            [2, "Chapter 1", 4],
            [2, "Chapter 2", 5],
            [2, "Chapter 3", 6],
            [3, "Section 3.1", 7],
            [4, "Section 3.1.1", 8],
            [2, "Chapter 4", 9],
            [2, "Chapter 5", 10],
            [1, "Part II: Advanced", 11],
            [2, "Chapter 6", 12],
            [2, "Chapter 7", 13],
            [1, "Appendix A", 14],
            [1, "Index", 15],
        ]

        mock_pdf = namedtuple("mock_pdf", "page_count")
        pdf = mock_pdf(len(test_toc))

        page_ranges_1 = pdf_splitter.get_page_ranges(pdf, test_toc, 1, False)
        self.assertEqual(page_ranges_1[0][0], "Copyright")
        self.assertEqual(page_ranges_1[1][1][0], 2)
        self.assertEqual(page_ranges_1[1][1][1], 2)

        # Nested sections are extracted correctly
        self.assertEqual(page_ranges_1[2][0], "Part I: Basics")
        self.assertEqual(page_ranges_1[2][1][0], 3)
        self.assertEqual(page_ranges_1[2][1][1], 10)

        self.assertEqual(page_ranges_1[3][0], "Part II: Advanced")
        self.assertEqual(page_ranges_1[3][1][0], 11)
        self.assertEqual(page_ranges_1[3][1][1], 13)

        # Last page is inserted correctly
        self.assertEqual(page_ranges_1[5][1][1], pdf.page_count - 1)

        self.assertEqual(len(page_ranges_1), 6)

        page_ranges_2 = pdf_splitter.get_page_ranges(pdf, test_toc, 2, False)
        self.assertEqual(page_ranges_2[2][0], "Chapter 3")
        self.assertEqual(page_ranges_2[2][1][0], 6)
        self.assertEqual(page_ranges_2[2][1][1], 8)

        self.assertEqual(page_ranges_2[6][0], "Chapter 7")
        self.assertEqual(page_ranges_2[6][1][0], 13)
        self.assertEqual(page_ranges_2[6][1][1], 13)

        self.assertEqual(len(page_ranges_2), 7)

        # Overlapping works
        page_ranges_3 = pdf_splitter.get_page_ranges(pdf, test_toc, 2, True)
        self.assertEqual(page_ranges_3[2][0], "Chapter 3")
        self.assertEqual(page_ranges_3[2][1][0], 6)
        self.assertEqual(page_ranges_3[2][1][1], 9)

        self.assertEqual(page_ranges_3[6][0], "Chapter 7")
        self.assertEqual(page_ranges_3[6][1][0], 13)
        self.assertEqual(page_ranges_3[6][1][1], 14)

        self.assertEqual(len(page_ranges_3), 7)

    def test_unnamed_toc(self):
        test_toc = [
            [1, "", 1],
            [1, "", 2],
            [1, "", 3],
            [2, "", 4],
            [2, "", 5],
            [2, "", 6],
            [3, "", 7],
            [4, "", 8],
            [2, "", 9],
            [2, "", 10],
            [1, "", 11],
            [2, "", 12],
            [2, "", 13],
            [1, "", 14],
            [1, "", 15],
        ]

        mock_pdf = namedtuple("mock_pdf", "page_count")
        pdf = mock_pdf(len(test_toc))

        page_ranges = pdf_splitter.get_page_ranges(pdf, test_toc, 1, False)
        self.assertEqual(page_ranges[0][0], "Untitled Section")
        self.assertEqual(page_ranges[1][0], "Untitled Section 2")
        self.assertEqual(page_ranges[2][0], "Untitled Section 3")
        self.assertEqual(page_ranges[3][0], "Untitled Section 4")
        self.assertEqual(page_ranges[4][0], "Untitled Section 5")
        self.assertEqual(page_ranges[5][0], "Untitled Section 6")

    def test_filter_by_regex(self):
        test_toc = [
            [1, "Copyright", 1],
            [1, "Table of Contents", 2],
            [1, "Part I: Basics", 3],
            [2, "Chapter 1", 4],
            [2, "Chapter 2", 5],
            [2, "Chapter 3", 6],
            [3, "Section 3.1", 7],
            [4, "Section 3.1.1", 8],
            [2, "Chapter 4", 9],
            [2, "Chapter 5", 10],
            [1, "Part II: Advanced", 11],
            [2, "Chapter 6", 12],
            [2, "Chapter 7", 13],
            [1, "Appendix A", 14],
            [1, "Index", 15],
        ]

        mock_pdf = namedtuple("mock_pdf", "page_count")
        pdf = mock_pdf(len(test_toc))

        page_ranges_1 = pdf_splitter.get_page_ranges(pdf, test_toc, 1, False)
        self.assertEqual(len(page_ranges_1), 6)

        filtered_1 = pdf_splitter.filter_by_regex(page_ranges_1, "^Part")
        self.assertEqual(len(filtered_1), 2)

        page_ranges_2 = pdf_splitter.get_page_ranges(pdf, test_toc, 2, False)
        self.assertEqual(len(page_ranges_2), 7)

        filtered_2 = pdf_splitter.filter_by_regex(page_ranges_2, "^Chapter [123]")
        self.assertEqual(len(filtered_2), 3)

    def test_safe_filename(self):
        self.assertEqual(pdf_splitter.safe_filename("file!@#$*'?`файл"), "fileфайл")


if __name__ == "__main__":
    unittest.main()
