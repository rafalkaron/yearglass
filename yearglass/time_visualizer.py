import math

from .usbprint import usbprint


class TimeVisualizer:
    def __init__(self, max_cols: int = 22, max_rows: int = 33):
        self.max_cols = max_cols
        self.max_rows = max_rows

    def render_hourglass(
        self,
        days_elapsed: int,
        days_total: int,
        symbol_elapsed: str = ".",
        symbol_remaining: str = ".",
        symbol_empty: str = " ",
    ) -> str:
        """
        Render a multiline string visualizing year progress as an hourglass.
        """

        def clamp_days(days_elapsed: int, days_total: int) -> tuple[int, int, int]:
            """
            Clamp days_total to not exceed total_cells, days_elapsed to not exceed days_total,
            and calculate days_remaining.
            Returns (days_elapsed, days_total, days_remaining)
            """
            total_cells: int = self.max_cols * self.max_rows
            days_total = min(days_total, total_cells)
            days_elapsed = min(days_elapsed, days_total)
            days_remaining: int = days_total - days_elapsed
            return days_elapsed, days_total, days_remaining

        days_elapsed, days_total, days_remaining = clamp_days(days_elapsed, days_total)

        def sort_rows(rows: list[str]) -> None:
            """
            Move the last row to follow the row with the closest (preferably same) length.
            Modifies the list in place.
            """
            if not rows or len(rows) < 2:
                return
            last_row: str = rows[-1]
            last_row_len = len(last_row)
            min_diff = None
            target_idx = None
            for idx, row in enumerate(rows[:-1]):
                diff = abs(len(row) - last_row_len)
                if min_diff is None or diff < min_diff:
                    min_diff = diff
                    target_idx = idx
                # Prefer exact match, break early
                if diff == 0:
                    break
            if target_idx is not None:
                # Remove last_row and insert after the closest row
                rows.pop(-1)
                rows.insert(target_idx + 1, last_row)

        # Top: days_remaining as a triangle (pyramid)
        remaining_rows: list[str] = []
        symbols_left = days_remaining
        row_width = 2
        while symbols_left > 0:
            # For all but the last row, use odd widths for triangle shape
            if symbols_left > row_width and row_width < self.max_cols:
                width = min(row_width, self.max_cols)
            else:
                width = min(symbols_left, self.max_cols)
            row = symbol_remaining * width
            remaining_rows.append(row)
            symbols_left -= width
            row_width += 2  # Next row is wider

        sort_rows(remaining_rows)
        remaining_rows.reverse()  # Reverse to have the largest row on top

        # Middle: empty rows
        def add_empty_rows(
            grid: list[str], remaining_rows: list[str], elapsed_rows: list[str]
        ) -> None:
            num_empty_rows = self.max_rows - len(remaining_rows) - len(elapsed_rows)
            if num_empty_rows > 0:
                grid.extend([symbol_empty * self.max_cols] * num_empty_rows)

        # Bottom: days_elapsed as a triangle (pyramid)
        elapsed_rows: list[str] = []
        symbols_left = days_elapsed
        row_width = 2
        while symbols_left > 0:
            # Use odd widths for triangle shape, but do not exceed max_cols
            width = min(row_width, self.max_cols, symbols_left)
            row = symbol_elapsed * width
            elapsed_rows.append(row)
            symbols_left -= width
            row_width += 2  # Next row is wider
        sort_rows(elapsed_rows)

        # Compose grid
        grid: list[str] = []
        grid.extend(remaining_rows)
        add_empty_rows(grid, remaining_rows, elapsed_rows)
        grid.extend(elapsed_rows)

        def center_row(row: str) -> str:
            content = row.rstrip()
            total_pad = self.max_cols - len(content)
            left = total_pad // 2
            right = total_pad - left
            return (symbol_empty * left) + content + (symbol_empty * right)

        grid = [center_row(r) for r in grid]

        hourglass: str = "\n".join(grid)
        usbprint(f"[render_yearglass]\n{hourglass}")
        return hourglass

    def render_level(
        self,
        days_elapsed: int,
        days_total: int,
        symbol_filled: str = "=",
        symbol_empty: str = " ",
    ) -> str:
        """
        Render a level indicator as a horizontal bar.
        """

        def calculate_rows_to_fill(days_elapsed: int, days_total: int) -> int:
            """
            Calculate the number of rows to fill based on the proportion of days elapsed to total days.
            Args:
                max_rows: The maximum number of rows available.
                days_elapsed: The number of days that have elapsed.
                days_total: The total number of days in the period.
            Returns:
                The number of rows to fill (int), rounded down.
            """
            if days_total <= 0 or self.max_rows <= 0 or days_elapsed < 0:
                return 0
            proportion = days_elapsed / days_total
            rows_to_fill = int(proportion * self.max_rows)
            usbprint(f"[calculate_rows_to_fill] Rows to fill: {rows_to_fill}")
            return rows_to_fill

        # Calculate bar dimensions
        rows_to_fill: int = calculate_rows_to_fill(days_elapsed, days_total)
        rows_to_empty: int = self.max_rows - rows_to_fill

        # Prepare the bar
        rows: list = []

        # Append empty rows
        for _ in range(rows_to_empty):
            row = symbol_empty * self.max_cols
            rows.append(row)

        # Append filled rows
        for _ in range(rows_to_fill):
            row = symbol_filled * self.max_cols
            rows.append(row)

        # Return the bar
        bar_str = "\n".join(rows)
        usbprint(f"[render_level]\n{bar_str}")
        return bar_str

    def render_piechart(
        self,
        days_elapsed: int,
        days_total: int,
        symbol_elapsed: str = "*",
        symbol_remaining: str = " ",
    ) -> str:
        """
        Render a rectangular pie chart (sector fill) as ASCII art, filling the entire rectangle.
        The fill starts at 12 o'clock and sweeps clockwise, proportional to year progress.
        """

        # Clamp days_total and days_elapsed
        total_cells = self.max_cols * self.max_rows
        days_total = min(days_total, total_cells)
        days_elapsed = min(days_elapsed, days_total)
        # Calculate progress (0.0 to 1.0)
        progress = days_elapsed / days_total if days_total > 0 else 0.0

        # Center of the rectangle
        cx = (self.max_cols - 1) / 2
        cy = (self.max_rows - 1) / 2

        # Angle to fill (in radians)
        angle_fill = 2 * math.pi * progress

        grid = []
        for y in range(self.max_rows):
            row = ""
            for x in range(self.max_cols):
                dx = x - cx
                dy = cy - y  # y axis is inverted for display
                theta = math.atan2(dx, dy)  # 0 at top, increases clockwise
                if theta < 0:
                    theta += 2 * math.pi
                if theta <= angle_fill:
                    row += symbol_elapsed
                else:
                    row += symbol_remaining
            grid.append(row)
        piechart = "\n".join(grid)
        usbprint(f"[render_piechart]\n{piechart}")
        return piechart

    def render_spiral(
        self,
        days_elapsed: int,
        days_total: int,
        symbol_elapsed: str = "+",
        symbol_remaining: str = " ",
    ) -> str:
        """
        Render a spiral progress: fills a rectangle in a spiral pattern as days pass.
        The spiral always fills the entire screen when all days pass, using proportions.
        """
        cols = self.max_cols
        rows = self.max_rows
        total_cells = cols * rows
        # Clamp days_total to total_cells, but use proportion for fill
        days_total = min(days_total, total_cells)
        # Calculate how many cells to fill for the current progress
        fill_cells = (
            int((days_elapsed / days_total) * total_cells) if days_total > 0 else 0
        )
        fill_cells = min(fill_cells, total_cells)
        # Prepare empty grid
        grid = [[symbol_remaining for _ in range(cols)] for _ in range(rows)]
        # Spiral fill
        top, left = 0, 0
        bottom, right = rows - 1, cols - 1
        count = 0
        while top <= bottom and left <= right and count < total_cells:
            # Top row
            for c in range(left, right + 1):
                if count < fill_cells:
                    grid[top][c] = symbol_elapsed
                count += 1
                if count >= total_cells:
                    break
            top += 1
            # Right col
            for r in range(top, bottom + 1):
                if count < fill_cells:
                    grid[r][right] = symbol_elapsed
                count += 1
                if count >= total_cells:
                    break
            right -= 1
            # Bottom row
            if top <= bottom:
                for c in range(right, left - 1, -1):
                    if count < fill_cells:
                        grid[bottom][c] = symbol_elapsed
                    count += 1
                    if count >= total_cells:
                        break
                bottom -= 1
            # Left col
            if left <= right:
                for r in range(bottom, top - 1, -1):
                    if count < fill_cells:
                        grid[r][left] = symbol_elapsed
                    count += 1
                    if count >= total_cells:
                        break
                left += 1
        spiral_str = "\n".join(["".join(row) for row in grid])
        usbprint(f"[render_spiral_progress]\n{spiral_str}")
        return spiral_str

    def render_crossout(
        self,
        days_elapsed: int,
        days_total: int,
        symbol_elapsed: str = "x",
        symbol_remaining: str = ".",
        symbol_empty: str = " ",
    ) -> str:
        """
        Render a single centered block of days_elapsed and days_remaining using symbol_elapsed and symbol_remaining.
        The block is filled left-to-right, top-to-bottom, and centered vertically in the grid.
        """
        total_cells = min(days_total, self.max_rows * self.max_cols)
        elapsed = min(days_elapsed, total_cells)
        remaining = total_cells - elapsed
        cells = [symbol_elapsed] * elapsed + [symbol_remaining] * remaining
        content_rows = []
        pad_left = 3
        pad_right = 3
        symbol_area = max(0, self.max_cols - pad_left - pad_right)
        for i in range(0, len(cells), symbol_area):
            row_cells = cells[i : i + symbol_area]
            row_cells += [symbol_empty] * (symbol_area - len(row_cells))
            row = (
                (symbol_empty * pad_left)
                + "".join(row_cells)
                + (symbol_empty * pad_right)
            )
            content_rows.append(row)
            if len(content_rows) >= self.max_rows:
                break
        # Vertically center the content_rows in max_rows
        total_content = len(content_rows)
        if total_content < self.max_rows:
            pad_top = (self.max_rows - total_content) // 2
            pad_bottom = self.max_rows - total_content - pad_top
            rows = (
                [symbol_empty * self.max_cols] * pad_top
                + content_rows
                + [symbol_empty * self.max_cols] * pad_bottom
            )
        else:
            rows = content_rows
        grid_str = "\n".join(rows)
        usbprint(f"[render_grid]\n{grid_str}")
        return grid_str

    def render_time_str(self, time_tuple: tuple) -> str:
        """
        Render a time tuple (year, month, day, hour, minute, second) as a formatted string.
        """
        t: str = f"{time_tuple[0]:04d}-{time_tuple[1]:02d}-{time_tuple[2]:02d} {time_tuple[3]:02d}:{time_tuple[4]:02d}:{time_tuple[5]:02d}"
        usbprint(f"[render_time_str] Rendered time string: {t}")
        return t
