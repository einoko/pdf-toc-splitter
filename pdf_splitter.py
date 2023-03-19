import re
import os
import sys
from typing import List, TypedDict
import click
import pypdf
import unicodedata


@click.command()
@click.option("--dry-run", is_flag=True, help="Simulate a split")
@click.option("--depth", nargs=1, default=1, show_default=True, help="Split depth")
@click.option(
    "--regex", nargs=1, help="Select outline items that match a RegEx pattern"
)
@click.option("--overlap", is_flag=True, help="Overlap split points")
@click.argument("file")
def main(dry_run: bool, depth: int, regex: str, overlap: bool, file: str):
    if not os.path.exists(file):
        print(f"Error: File '{file}' does not exist.")
        sys.exit(1)

    try:
        pdf = pypdf.PdfReader(file)
    except:
        print("Error: File is not a valid PDF.")
        sys.exit(1)

    if len(pdf.outline) == 0:
        print("Error: File does not contain an outline.")
        sys.exit(0)

    toc = get_toc(pdf)

    page_count = len(pdf.pages)
    page_ranges = prepare_page_ranges(toc, depth, regex, overlap, page_count)

    if len(page_ranges) == 0:
        if regex is None:
            print("No outline items match the current depth.")
        else:
            print("No outline items match the current depth or RegEx.")
    else:
        if dry_run is True:
            dry_run_toc_split(page_ranges)
        else:
            split_pdf(pdf, page_ranges)


class OutlineItem(TypedDict):
    name: str
    page: int
    level: int


def get_toc(pdf: pypdf.PdfReader) -> List[OutlineItem]:
    toc_list = []

    def extract_toc(toc, level=1):
        for item in toc:
            if type(item) != list:
                if item["/Title"] is None:
                    continue

                item_obj = {
                    "name": unicodedata.normalize(
                        "NFKD",
                        item["/Title"].strip().replace("\r",
                                                       " ").replace("\t", " ").replace("\n", " "),
                    ),
                    "page": pdf.get_destination_page_number(item),
                    "level": level
                }

                if len([item for item in toc_list if item == item_obj]) == 0:
                    toc_list.append(item_obj)
            else:
                for item in toc:
                    extract_toc(item, level + 1)

    extract_toc(pdf.outline)

    toc_list = sorted(toc_list, key=lambda k: (k["page"], k["level"]))
    return toc_list


class PageRange(TypedDict):
    name: str
    page_range: tuple


def prepare_page_ranges(toc: List[OutlineItem], depth: int, regex: str, overlap: int, page_count: int) -> List[PageRange]:
    page_ranges = get_page_ranges(toc, depth, overlap, page_count)

    if regex is not None:
        page_ranges = filter_by_regex(page_ranges, regex)

    return page_ranges


def get_page_ranges(toc: List[OutlineItem], depth: int, overlap: bool, page_count: int) -> List[PageRange]:
    filtered_toc = get_n_levels(toc, depth)
    page_ranges = []

    for i, item in enumerate(filtered_toc):
        name = item["name"]

        # Handle empty outline entries
        if len(name) == 0:
            name = "Untitled Section"

        # Handle duplicate outline entries
        if len([item for item in page_ranges if name is item["name"]]) > 0:
            name += " {}".format(
                len([item for item in page_ranges if name in item["name"]]) + 1
            )

        if item["level"] == depth and i < len(filtered_toc) - 1:
            if overlap:
                page_ranges.append(
                    {
                        "name": name,
                        "page_range": (item["page"], filtered_toc[i + 1]["page"]),
                    }
                )
            else:
                page_ranges.append(
                    {
                        "name": name,
                        "page_range": (
                            item["page"],
                            filtered_toc[i + 1]["page"] - 1
                            if filtered_toc[i + 1]["page"] > item["page"]
                            else item["page"]
                        ),
                    }
                )
        elif item["level"] == depth and i == len(filtered_toc) - 1:
            page_ranges.append(
                {"name": name, "page_range": (item["page"], page_count - 1)}
            )

    return page_ranges


def split_pdf(pdf: pypdf.PdfReader, page_ranges: List[PageRange]):
    for page_range in page_ranges:
        pdf_writer = pypdf.PdfWriter()
        pdf_writer.append(fileobj=pdf, pages=(
            page_range["page_range"][0], page_range["page_range"][1] + 1))
        filename = "{}.pdf".format(safe_filename(page_range["name"]))
        output = open(filename, "wb")
        pdf_writer.write(output)

        print("Created file '{}'".format(filename))


def dry_run_toc_split(page_ranges: List[PageRange]):
    print("With current options, the following PDF files would be created.\n")

    for item in page_ranges:
        if item["page_range"][0] == item["page_range"][1]:
            print(
                "– {}.pdf (contains page {})".format(
                    safe_filename(item["name"]), item["page_range"][0] + 1
                )
            )
        else:
            print(
                "– {}.pdf (contains pages {}–{})".format(
                    safe_filename(item["name"]),
                    item["page_range"][0] + 1,
                    item["page_range"][1] + 1,
                )
            )


def safe_filename(filename: str) -> str:
    return "".join(
        c for c in filename if c.isalnum() or c in (" ", ".", "_", "-")
    ).rstrip()


def filter_by_regex(input_list: List[PageRange], regex: str) -> List[PageRange]:
    return [item for item in input_list if re.search(r"{}".format(regex), item["name"])]


def get_n_levels(input_list: List[OutlineItem], level: int) -> List[OutlineItem]:
    return [item for item in input_list if item["level"] <= level]


if __name__ == "__main__":
    main()
