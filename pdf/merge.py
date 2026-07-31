from pypdf import PdfWriter


def merge_pdf(files, output):

    writer = PdfWriter()

    for file in files:
        writer.append(file)

    with open(output, "wb") as f:
        writer.write(f)

    return output