from docling.document_converter import DocumentConverter
import json

converter = DocumentConverter()

result = converter.convert(
    r"D:\projects\classloggerRAG\data\question papers\23DC6PCSEA (2) (1).pdf"
)

data = result.document.export_to_dict()

current_unit = None
current_question_no = None

for table_no, table in enumerate(data["tables"]):

    print("\n" + "=" * 100)
    print(f"TABLE {table_no}")
    print("=" * 100)

    grid = table["data"]["grid"]

    for row_no, row in enumerate(grid):

        cells = [cell["text"].strip() for cell in row]

        print("\n")
        print("-" * 80)
        print(f"ROW {row_no}")
        print(cells)

        try:

            if len(cells) < 6:
                print("SKIPPED: less than 6 columns")
                continue

            # Skip obvious garbage/header rows
            if "blank" in cells:
                print("SKIPPED: blank row")
                continue

            if "CO" in cells and "PO" in cells:
                print("SKIPPED: header row")
                continue

            if "Marks" in cells:
                print("SKIPPED: marks header row")
                continue

            # Detect UNIT anywhere in row
            unit_cell = next(
                (cell for cell in cells if "UNIT" in cell.upper()),
                None
            )

            if unit_cell:
                current_unit = unit_cell
                print(f"UNIT FOUND -> {current_unit}")
                continue

            question_no = cells[0]
            subquestion = cells[1]
            question_text = cells[2]
            co_type = cells[3]
            po_type = cells[4]
            marks = cells[5]

            print(f"question_no = {repr(question_no)}")
            print(f"subquestion = {repr(subquestion)}")
            print(f"question_text = {repr(question_text)}")
            print(f"co_type = {repr(co_type)}")
            print(f"po_type = {repr(po_type)}")
            print(f"marks = {repr(marks)}")

            # OR rows
            if "OR" in cells:
                print("OR ROW")
                continue

            # Question number
            if question_no.isdigit():
                current_question_no = int(question_no)
                print(f"QUESTION NUMBER = {current_question_no}")
            else:
                print(f"NOT A QUESTION NUMBER: {question_no}")

            # Marks
            if not marks.isdigit():
                print(f"INVALID MARKS: {marks}")
                continue

            marks_int = int(marks)

            document = {
                "question_id": str(current_question_no),
                "question_no": current_question_no,
                "subpart": subquestion,
                "unit": current_unit,
                "question": question_text,
                "co": co_type,
                "po": po_type,
                "marks": marks_int
            }

            print(document)

        except Exception as e:

            print("\n" + "#" * 100)
            print("FAILED ROW")
            print(f"TABLE = {table_no}")
            print(f"ROW = {row_no}")
            print(f"CELLS = {cells}")
            print(f"ERROR = {e}")
            print("#" * 100)

            continue