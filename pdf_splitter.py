import re
import os
import sys
import click
import fitz
import unicodedata


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
        print("Error: File {} does not exist.".format(file))
        sys.exit(1)

    pdf = fitz.open(file)
    toc = pdf.get_toc()

    if len(toc) == 0:
        print("Table of contents was not found in the PDF file. Exiting.")
        sys.exit(0)

    toc = [
        {
            "level": x[0],
            "name": unicodedata.normalize(
                "NFKD",
                x[1].strip().replace("\r", " ").replace("\t", " ").replace("\n", " "),
            ),
            "page": x[2] - 1,
        }
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
                        "page_range": (item["page"], filtered_toc[i + 1]["page"] - 1),
                    }
                )
        elif item["level"] == depth and i == len(filtered_toc) - 1:
            page_ranges.append(
                {"name": name, "page_range": (item["page"], pdf.page_count - 1)}
            )

    return page_ranges


def split_pdf(pdf, page_ranges):
    for page_range in page_ranges:
        document = fitz.open()
        document.insert_pdf(
            pdf,
            from_page=page_range["page_range"][0],
            to_page=page_range["page_range"][1],
            links=True,
            annots=True,
        )
        filename = "{}.pdf".format(safe_filename(page_range["name"]))
        document.save(filename)
        print("Created file {}".format(filename))


def simulate_toc_split(page_ranges):
    print("With current options, the following PDF files would be created.\n")

    for item in page_ranges:
        if item["page_range"][0] == item["page_range"][1]:
            print(
                "– {}.pdf (contains page {})".format(
                    safe_filename(item["name"]), item["page_range"][0]
                )
            )
        else:
            print(
                "– {}.pdf (contains pages {}–{})".format(
                    safe_filename(item["name"]),
                    item["page_range"][0],
                    item["page_range"][1],
                )
            )


def safe_filename(filename):
    return "".join(
        [c for c in filename if c.isalpha() or c.isdigit() or c == " "]
    ).rstrip()


def filter_by_regex(input_list, regex):
    return [item for item in input_list if re.search(r"{}".format(regex), item["name"])]


def get_n_levels(input_list, level):
    return [item for item in input_list if item["level"] <= level]


if __name__ == "__main__":
    main()
