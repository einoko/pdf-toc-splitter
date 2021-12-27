import re
import os
import sys
import click
import fitz
import unicodedata
from slugify import slugify


@click.command()
@click.option("--simulate", is_flag=True, help="Simulate a split")
@click.option("--depth", nargs=1, default=1, show_default=True, help="Split depth")
@click.option(
    "--regex", nargs=1, help="Select outline items that match a RegEx pattern"
)
@click.option("--overlap", is_flag=True, help="Overlap split points")
@click.argument("file")
def main(simulate, depth, regex, overlap, file):
    if not os.path.exists(file):
        print("File {} does not exist.".format(file))
        sys.exit()

    pdf = fitz.open(file)
    toc = pdf.get_toc()

    if len(toc) == 0:
        print("Could not read the table of contents.")
        sys.exit()

    toc = [
        [
            x[0],
            unicodedata.normalize(
                "NFKD",
                x[1].strip().replace("\r", " ").replace("\t", " ").replace("\n", " "),
            ),
            x[2] - 1,
        ]
        for x in toc
    ]

    page_ranges = prepare_page_ranges(pdf, toc, depth, regex, overlap)

    if len(page_ranges) == 0:
        if regex is None:
            print("No outline items match the current depth.")
        else:
            print("No outline items match the current depth or RegEx.")
    else:
        if simulate is True:
            simulate_toc_split(page_ranges)
        else:
            split_pdf(pdf, page_ranges)


def prepare_page_ranges(pdf, toc, depth, regex, overlap):
    page_ranges = get_page_ranges(pdf, toc, depth, overlap)

    if regex is not None:
        page_ranges = filter_by_regex(page_ranges, regex)

    return page_ranges


def get_page_ranges(pdf, toc, depth, overlap):
    filtered_toc = get_n_levels(toc, depth)
    page_ranges = []

    for i, item in enumerate(filtered_toc):
        if item[0] == depth and i < len(filtered_toc) - 1:
            name = item[1]

            # Handle empty outline entries
            if len(name) == 0:
                name = "Untitled"

            # Handle duplicate outline entries
            if len([item for item in page_ranges if name == item[0]]) > 0:
                name += "_{}".format(
                    len([item for item in page_ranges if name is item]) + 2
                )

            if overlap:
                page_ranges.append([name, (item[2], filtered_toc[i + 1][2])])
            else:
                page_ranges.append([name, (item[2], filtered_toc[i + 1][2] - 1)])
        elif item[0] == depth and i == len(filtered_toc) - 1:
            page_ranges.append([item[1], (item[2], pdf.page_count)])

    return page_ranges


def split_pdf(pdf, page_ranges):
    for range in page_ranges:
        document = fitz.open()
        document.insert_pdf(
            pdf, from_page=range[1][0], to_page=range[1][1], links=True, annots=True
        )
        filename = "{}.pdf".format(slugify(range[0]))
        document.save(filename)
        print("Created file {}".format(filename))


def simulate_toc_split(page_ranges):
    print("With current options, the following PDF files would be created.\n")

    for item in page_ranges:
        print(
            "{}.pdf (contains pages {}–{})".format(
                slugify(item[0]), item[1][0], item[1][1]
            )
        )


def filter_by_regex(input_list, regex):
    return [item for item in input_list if re.search(r"{}".format(regex), item[0])]


def get_n_levels(input_list, level):
    return [item for item in input_list if item[0] <= level]


if __name__ == "__main__":
    main()
