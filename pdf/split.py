from pypdf import PdfReader, PdfWriter


def split_pdf(
    input_file,
    start_page,
    end_page,
    output_file
):

    reader = PdfReader(
        input_file
    )

    writer = PdfWriter()


    for page in range(
        start_page - 1,
        end_page
    ):

        writer.add_page(
            reader.pages[page]
        )


    with open(
        output_file,
        "wb"
    ) as f:

        writer.write(f)


    return output_file