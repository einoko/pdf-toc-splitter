import os
import re
import sys
import unicodedata
from typing import List, TypedDict

import click
import pypdf


@click.command()
@click.option("--dry-run", is_flag=True, help="Simulate a split")
@click.option("--depth", nargs=1, default=1, show_default=True, help="Split depth")
@click.option("--max-filename-length", nargs=1 , default=0, show_default=True,
              help="Maximum filename length. The default 0 indicates no limit.")
@click.option(
    "--regex", nargs=1, help="Select outline items that match a RegEx pattern"
)
@click.option("--overlap", is_flag=True, help="Overlap split points")
@click.option(
    "--prefix",
    nargs=1,
    help="Filename prefix. Supports the {n} placeholder for an n-th item index.",
)
@click.argument("file")
def main(dry_run: bool, depth: int, max_filename_length: int, regex: str, overlap: bool, prefix: str, file: str):
    if not os.path.exists(file):
        print(f"Error: File '{file}' does not exist.")
        sys.exit(1)

    try:
        pdf = pypdf.PdfReader(file)
    except Exception:
        print("Error: File is not a valid PDF.")
        sys.exit(1)

    if len(pdf.outline) == 0:
        print("Error: File does not contain an outline.")
        sys.exit(1)

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
            dry_run_toc_split(page_ranges, prefix, max_filename_length)
        else:
            split_pdf(pdf, page_ranges, prefix, max_filename_length)


class OutlineItem(TypedDict):
    name: str
    page: int
    level: int


def get_toc(pdf: pypdf.PdfReader) -> List[OutlineItem]:
    toc_list = []

    def extract_toc(toc, level=1):
        for item in toc:
            if not isinstance(item, list):
                if item["/Title"] is None:
                    continue

                item_obj = {
                    "name": unicodedata.normalize(
                        "NFKD",
                        item["/Title"]
                        .strip()
                        .replace("\r", " ")
                        .replace("\t", " ")
                        .replace("\n", " "),
                    ),
                    "page": pdf.get_destination_page_number(item),
                    "level": level,
                }

                if item_obj not in toc_list:
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


def prepare_page_ranges(
    toc: List[OutlineItem], depth: int, regex: str, overlap: bool, page_count: int
) -> List[PageRange]:
    page_ranges = get_page_ranges(toc, depth, overlap, page_count)

    if regex is not None:
        page_ranges = filter_by_regex(page_ranges, regex)

    return page_ranges


def get_page_ranges(
    toc: List[OutlineItem], depth: int, overlap: bool, page_count: int
) -> List[PageRange]:
    filtered_toc = get_n_levels(toc, depth)
    page_ranges = []

    for i, item in enumerate(filtered_toc):
        name = item["name"]

        # Handle empty outline entries
        if len(name) == 0:
            name = "Untitled Section"

        # Handle duplicate outline entries
        if any(item["name"] == name for item in page_ranges):
            name += f" {sum(1 for item in page_ranges if name in item['name']) + 1}"

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
                            else item["page"],
                        ),
                    }
                )
        elif item["level"] == depth and i == len(filtered_toc) - 1:
            page_ranges.append(
                {"name": name, "page_range": (item["page"], page_count - 1)}
            )

    return page_ranges


def split_pdf(pdf: pypdf.PdfReader, page_ranges: List[PageRange], prefix: str, maximum_file_name_length: int):
    width = len(str(len(page_ranges)))
    for i, page_range in enumerate(page_ranges):
        pdf_writer = pypdf.PdfWriter()
        pdf_writer.append(
            fileobj=pdf,
            pages=(page_range["page_range"][0], page_range["page_range"][1] + 1),
        )

        filename = f"{safe_filename(page_range['name'])}.pdf"
        if prefix:
            if "{n}" in prefix:
                formatted_prefix = prefix.replace("{n}", f"{i + 1:0{width}d}")
                filename = f"{safe_filename(formatted_prefix)}{filename}"
            else:
                filename = f"{safe_filename(prefix)}{filename}"

        filename = shorten_filename_if_required(filename, maximum_file_name_length)
        with open(filename, "wb") as output:
            pdf_writer.write(output)

        print(f"Created file '{filename}'")


def dry_run_toc_split(page_ranges: List[PageRange], prefix: str,  maximum_file_name_length: int):
    print("With current options, the following PDF files would be created.\n")

    width = len(str(len(page_ranges)))
    for i, item in enumerate(page_ranges):
        filename = safe_filename(item["name"])

        if prefix:
            if "{n}" in prefix:
                formatted_prefix = prefix.replace("{n}", f"{i + 1:0{width}d}")
                filename = f"{safe_filename(formatted_prefix)}{filename}"
            else:
                filename = f"{safe_filename(prefix)}{filename}"

        filename = shorten_filename_if_required(filename + ".pdf", maximum_file_name_length)
        if item["page_range"][0] == item["page_range"][1]:
            print(f"– {filename} (contains page {item['page_range'][0] + 1})")
        else:
            print(
                f"– {filename} (contains pages {item['page_range'][0] + 1}–{item['page_range'][1] + 1})"
            )


def safe_filename(filename: str) -> str:
    return "".join(c for c in filename if c.isalnum() or c in (" ", ".", "_", "-"))

def shorten_filename_if_required(filename: str, file_name_max_len: int = 25) -> str:
    if file_name_max_len == 0:
        return filename
    modified_file_name = filename
    if len(modified_file_name) > file_name_max_len:
        basename, ext = os.path.splitext(modified_file_name)
        modified_file_name = basename[:(file_name_max_len - len(ext))].rstrip() + ext
    return modified_file_name


def filter_by_regex(input_list: List[PageRange], regex: str) -> List[PageRange]:
    return [item for item in input_list if re.search(regex, item["name"])]


def get_n_levels(input_list: List[OutlineItem], level: int) -> List[OutlineItem]:
    return [item for item in input_list if item["level"] <= level]


if __name__ == "__main__":
    main()
