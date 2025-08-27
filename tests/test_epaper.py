import utime as time  # type: ignore

from yearglass.epaper import EPaper


class TestEPaper:
    def __init__(self):
        self.epaper = EPaper()

    def test_display_text(self):
        self.epaper.display_text("Hello, ePaper!", x=0, y=0)
        print("Displayed: Hello, ePaper!")
        time.sleep(2)

    def test_display_text_row(self):
        self.epaper.display_text_row("Row 5", row=5)
        print("Displayed: Row 5 at row 5")
        time.sleep(2)

    def test_display_text_rows(self):
        text = "Row1\nRow2\nRow3"
        self.epaper.display_text_rows(text)
        print("Displayed 3 rows of text")
        time.sleep(2)

    def test_display_text_sentence(self):
        text = "This is a test sentence that should wrap across multiple rows on the e-paper display."
        self.epaper.display_text_sentence(text)
        print("Displayed wrapped sentence")
        time.sleep(2)

    def test_display_text_row_too_long(self):
        # Exceeds max_columns
        long_text = "X" * (self.epaper.max_columns + 10)
        self.epaper.display_text_row(long_text, row=0)
        print("Displayed: Truncated long row text")
        time.sleep(2)

    def test_display_text_rows_too_many(self):
        # Exceeds max_rows
        many_rows = "\n".join([f"Row{i}" for i in range(self.epaper.max_rows + 5)])
        self.epaper.display_text_rows(many_rows)
        print("Displayed: Truncated many rows text")
        time.sleep(2)

    def test_display_text_sentence_too_long(self):
        # Exceeds both columns and rows
        long_sentence = " ".join(
            ["word"] * (self.epaper.max_columns * (self.epaper.max_rows + 10))
        )
        self.epaper.display_text_sentence(long_sentence)
        print("Displayed: Truncated long sentence")
        time.sleep(2)

    def run_all(self):
        self.test_display_text()
        self.test_display_text_row()
        self.test_display_text_rows()
        self.test_display_text_sentence()
        self.test_display_text_row_too_long()
        self.test_display_text_rows_too_many()
        self.test_display_text_sentence_too_long()


if __name__ == "__main__":
    test = TestEPaper()
    test.run_all()
