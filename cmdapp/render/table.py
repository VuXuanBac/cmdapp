from ..utils import Terminal

from cmd2 import table_creator as tabling


class Tabling:
    STYLE = ["Simple", "Bordered", "Alternating"]

    def get_single_column_width(number_of_parts: int):
        return int(Terminal.width() * 0.7 // number_of_parts)

    def _create_columns(headers: list[str], widths: list[int]):
        n_columns = len(headers)
        widths = (widths or [])[:n_columns] + [1] * (n_columns - len(widths or []))
        single_width = Tabling.get_single_column_width(sum(widths))
        return [
            tabling.Column(
                header,
                width=w * single_width,
                header_horiz_align=tabling.HorizontalAlignment.CENTER,
            )
            for header, w in zip(headers, widths)
        ]

    def generate(data: list[dict], style="Simple", widths=None, headers=None):
        if isinstance(style, int):
            style = __class__.STYLE[max(0, min(len(__class__.STYLE) - 1, style))]
        if not headers:
            if not data:
                return ""
            headers = list(data[0])
        table_class = getattr(
            tabling, f"{str(style).title()}Table", tabling.SimpleTable
        )
        columns = __class__._create_columns(headers, widths)
        table = table_class(columns).generate_table([list(d.values()) for d in data])
        return table
