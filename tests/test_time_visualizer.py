from yearglass.time_visualizer import TimeVisualizer


class TestTimeVisualizer:
    def __init__(self):
        self.time_visualizer = TimeVisualizer()

    def test_render_crossout_zero_elapsed(self):
        print("[Crossout: 0 elapsed]")
        result = self.time_visualizer.render_crossout(
            0, 365, symbol_elapsed="*", symbol_remaining="."
        )
        assert result.count("*") == 0
        assert result.count(".") == 365

    def test_render_crossout_all_elapsed(self):
        print("[Crossout: All elapsed]")
        result = self.time_visualizer.render_crossout(
            365, 365, symbol_elapsed="*", symbol_remaining="."
        )
        assert result.count("*") == 365
        assert result.count(".") == 0

    def test_render_crossout_half_elapsed(self):
        print("[Crossout: Half elapsed]")
        result = self.time_visualizer.render_crossout(
            182, 365, symbol_elapsed="*", symbol_remaining="."
        )
        assert result.count("*") == 182
        assert result.count(".") == 183

    def test_render_spiral_zero_elapsed(self):
        print("[Spiral Progress: 0 elapsed]")
        result = self.time_visualizer.render_spiral(
            0, 365, symbol_elapsed="*", symbol_remaining="."
        )
        total_cells = self.time_visualizer.max_cols * self.time_visualizer.max_rows
        assert isinstance(result, str)
        assert result.count("*") == 0
        assert result.count(".") == total_cells

    def test_render_spiral_all_elapsed(self):
        print("[Spiral Progress: All elapsed]")
        result = self.time_visualizer.render_spiral(
            365, 365, symbol_elapsed="*", symbol_remaining="."
        )
        total_cells = self.time_visualizer.max_cols * self.time_visualizer.max_rows
        assert result.count("*") == total_cells
        assert result.count(".") == 0

    def test_render_spiral_half_elapsed(self):
        print("[Spiral Progress: Half elapsed]")
        result = self.time_visualizer.render_spiral(
            182, 365, symbol_elapsed="*", symbol_remaining="."
        )
        total_cells = self.time_visualizer.max_cols * self.time_visualizer.max_rows
        expected_filled = int((182 / 365) * total_cells)
        assert abs(result.count("*") - expected_filled) <= 1  # allow rounding error
        assert result.count(".") == total_cells - result.count("*")

    def test_render_hourglass_zero_elapsed(self):
        print("[Yearglass: 0 elapsed]")
        result = self.time_visualizer.render_hourglass(0, 365)
        assert isinstance(result, str)
        assert result.count("*") == 365

    def test_render_hourglass_all_elapsed(self):
        print("[Yearglass: All elapsed]")
        result_full = self.time_visualizer.render_hourglass(365, 365)
        assert result_full.count("*") == 365

    def test_render_hourglass_half_elapsed(self):
        print("[Yearglass: Half elapsed]")
        result_half = self.time_visualizer.render_hourglass(182, 365)
        assert result_half.count("*") == 365

    def test_render_time_str_normal(self):
        t = (2025, 8, 17, 12, 34, 56)
        s = self.time_visualizer.render_time_str(t)
        print(f"[Time str] {s}")
        assert s == "2025-08-17 12:34:56"

    def test_render_time_str_zero_padding(self):
        t2 = (2025, 1, 2, 3, 4, 5)
        s2 = self.time_visualizer.render_time_str(t2)
        print(f"[Time str zero pad] {s2}")
        assert s2 == "2025-01-02 03:04:05"

    def test_render_level_zero_elapsed(self):
        print("[Level: 0 elapsed]")
        result = self.time_visualizer.render_level(0, 100, symbol_filled="*")
        assert result.count("*") == 0

    def test_render_level_all_elapsed(self):
        print("[Level: All elapsed]")
        result = self.time_visualizer.render_level(10, 10, symbol_filled="*")
        assert result.count("*") == 726

    def test_render_level_half_elapsed(self):
        print("[Level: Half elapsed]")
        result = self.time_visualizer.render_level(5, 10, symbol_filled="*")
        assert result.count("*") == 352

    def test_render_piechart_zero_elapsed(self):
        print("[Piechart: 0 elapsed]")
        result = self.time_visualizer.render_piechart(
            0, 365, symbol_elapsed="*", symbol_remaining="."
        )
        assert isinstance(result, str)
        # Should contain no '*' and many '.'
        assert result.count("*") == 0
        assert result.count(".") > 0

    def test_render_piechart_all_elapsed(self):
        print("[Piechart: All elapsed]")
        result = self.time_visualizer.render_piechart(
            365, 365, symbol_elapsed="*", symbol_remaining="."
        )
        # Should fill all possible area inside the ellipse
        assert result.count("*") > 0
        # Should have fewer '.' than total area
        assert (
            result.count("*") + result.count(".")
            >= self.time_visualizer.max_cols * self.time_visualizer.max_rows
        )

    def test_render_piechart_half_elapsed(self):
        print("[Piechart: Half elapsed]")
        result = self.time_visualizer.render_piechart(
            182, 365, symbol_elapsed="*", symbol_remaining="."
        )
        # Should have some '*' and some '.'
        assert result.count("*") > 0
        assert result.count(".") > 0

    def run_all(self):
        self.test_render_time_str_normal()
        self.test_render_time_str_zero_padding()

        self.test_render_level_all_elapsed()
        self.test_render_level_zero_elapsed()
        self.test_render_level_half_elapsed()

        self.test_render_piechart_zero_elapsed()
        self.test_render_piechart_all_elapsed()
        self.test_render_piechart_half_elapsed()

        self.test_render_hourglass_zero_elapsed()
        self.test_render_hourglass_all_elapsed()
        self.test_render_hourglass_half_elapsed()

        self.test_render_spiral_zero_elapsed()
        self.test_render_spiral_all_elapsed()
        self.test_render_spiral_half_elapsed()

        self.test_render_crossout_zero_elapsed()
        self.test_render_crossout_all_elapsed()
        self.test_render_crossout_half_elapsed()


if __name__ == "__main__":
    test = TestTimeVisualizer()
    test.run_all()
