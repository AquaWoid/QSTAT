import pathlib
from docling.document_converter import DocumentConverter


def pdf_ingest(path : str, export_format : str = "markdown"):

    data = pathlib.Path(path)
    

    for file in data.iterdir():
        if(file.suffix == ".pdf"):

            source = file
            converter = DocumentConverter()
            doc = converter.convert(file).document

            print(doc.export_to_markdown())
            if export_format == "markdown":
                return doc.export_to_markdown()

            #doc_to_chunk = doc

