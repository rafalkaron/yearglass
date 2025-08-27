from libs.Pico_ePaper_2_7 import EPD_2in7 as EPD


class EPaper:
    """Wrapper for the official Waveshare Pico_ePaper_2_7 driver.
    Displays black and white text in portait mode (176px x 264px).
    Supports up to 22 characters per one of 33 lines (8px x 8px font).
    """

    def __init__(self) -> None:
        self.epd = EPD()
        self.max_rows: int = 33
        self.max_columns: int = 22
        self.font_size: int = 8

    def display_text(self, text: str, x: int = 0, y: int = 0) -> None:
        """
        Display a text string on the e-paper display at the given position.
        """
        self.epd.EPD_2IN7_Init_4Gray()
        self.epd.image4Gray.fill(self.epd.white)
        self.epd.image4Gray.text(text, x, y, self.epd.black)
        self.epd.EPD_2IN7_4Gray_Display(self.epd.buffer_4Gray)
        self.epd.Sleep()

    def display_text_row(self, text: str, row: int = 0) -> None:
        """
        Displays text at a specific row. Raises ValueError if out of bounds.
        """
        if not (0 <= row < self.max_rows):
            raise ValueError(f"Row {row} is out of range (0-{self.max_rows - 1}).")
        if len(text) > self.max_columns:
            print(
                f"Warning: text exceeds {self.max_columns} characters and will be truncated."
            )
            text = text[: self.max_columns]
        x = 0
        y = row * self.font_size
        self.display_text(text, x, y)

    def display_text_rows(self, text: str) -> None:
        """
        Display multiline text.
        Raises ValueError if too many rows.
        """
        rows = text.splitlines()
        if len(rows) > self.max_rows:
            print(
                f"Warning: text has {len(rows)} rows, but only {self.max_rows} can be displayed. Extra rows will be ignored."
            )
            rows = rows[: self.max_rows]
        for i, row in enumerate(rows):
            if len(row) > self.max_columns:
                print(
                    f"Warning: row {i} exceeds {self.max_columns} characters and will be truncated."
                )
                rows[i] = row[: self.max_columns]
        self.epd.EPD_2IN7_Init_4Gray()
        self._update_buffer_rows(rows)
        self.epd.EPD_2IN7_4Gray_Display(self.epd.buffer_4Gray)
        self.epd.Sleep()

    def display_text_sentence(self, text: str) -> None:
        """
        Format a passed sentence to fit display, wrapping words to new lines without splitting them.
        """
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line) == 0:
                if len(word) > self.max_columns:
                    lines.append(word[: self.max_columns])
                    rest = word[self.max_columns :]
                    while len(rest) > 0:
                        lines.append(rest[: self.max_columns])
                        rest = rest[self.max_columns :]
                else:
                    current_line = word
            elif len(current_line) + 1 + len(word) <= self.max_columns:
                current_line += " " + word
            else:
                lines.append(current_line)
                if len(word) > self.max_columns:
                    lines.append(word[: self.max_columns])
                    rest = word[self.max_columns :]
                    while len(rest) > 0:
                        lines.append(rest[: self.max_columns])
                        rest = rest[self.max_columns :]
                    current_line = ""
                else:
                    current_line = word
        if current_line:
            lines.append(current_line)
        if len(lines) > self.max_rows:
            print(
                f"Warning: sentence wrapped to {len(lines)} lines, but only {self.max_rows} can be displayed. Extra lines will be ignored."
            )
            lines = lines[: self.max_rows]
        self.display_text_rows("\n".join(lines))

    def _update_buffer_rows(self, lines) -> None:
        self.epd.image4Gray.fill(self.epd.white)
        for i, row in enumerate(lines[: self.max_rows]):
            x = 0
            y = i * self.font_size
            self.epd.image4Gray.text(row, x, y, self.epd.black)
