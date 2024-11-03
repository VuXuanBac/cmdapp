import bogo
import re
from datetime import datetime, timedelta

TIME_DELTA_REGEX = r"([\+-><])(\d+)\.(day|second|minute|hour|week)s?"


class Text:
    def convert_to_datetime(datetime_str: str):
        r"""Support formats:
        - keywords: now, today
        - timedelta: (+|-)(\d+)\.(\w+)
        - timeformat: %Y%m%d%H%M%S%f
        """
        # Keywords
        if datetime_str == "now":
            return datetime.now()
        if datetime_str == "today":
            return datetime.today()

        # Time delta
        match_timedelta = re.match(TIME_DELTA_REGEX, datetime_str)
        if match_timedelta:
            is_add = match_timedelta.group(1) not in ["-", "<"]
            delta = match_timedelta.group(2)
            unit = match_timedelta.group(3) + "s"
            time_delta = timedelta(**{unit: float(delta)})
            return (
                datetime.now() + time_delta if is_add else datetime.now() - time_delta
            )

        # Format
        datetime_str = re.sub(r"\D+", "", datetime_str)
        FORMAT = "%Y%m%d%H%M%S%f"  # 4 + 2 + 2 + 2 + 2 + 2 + 6 = 20
        if len(datetime_str) == 6:
            datetime_str = "20" + datetime_str + "0" * 12
        elif len(datetime_str) >= 8 and len(datetime_str) < 20:
            datetime_str = datetime_str + "0" * (20 - len(datetime_str))
        if len(datetime_str) == 20:
            return datetime.strptime(datetime_str, FORMAT)
        raise ValueError(
            f"datetime string [{datetime_str}] is invalid",
            rf"try: [now, today, \d+.days, -\d+.weeks,... or {FORMAT}]",
        )

    def convert_to_telex(text: str):
        return bogo.process_sequence(text)

    def convert_to_ascii(text: str):
        text = re.sub(r"A|Á|À|Ã|Ạ|Â|Ấ|Ầ|Ẫ|Ậ|Ă|Ắ|Ằ|Ẵ|Ặ", "A", text)
        text = re.sub(r"à|á|ạ|ả|ã|â|ầ|ấ|ậ|ẩ|ẫ|ă|ằ|ắ|ặ|ẳ|ẵ", "a", text)
        text = re.sub(r"E|É|È|Ẽ|Ẹ|Ê|Ế|Ề|Ễ|Ệ/", "E", text)
        text = re.sub(r"è|é|ẹ|ẻ|ẽ|ê|ề|ế|ệ|ể|ễ", "e", text)
        text = re.sub(r"I|Í|Ì|Ĩ|Ị", "I", text)
        text = re.sub(r"ì|í|ị|ỉ|ĩ", "i", text)
        text = re.sub(r"O|Ó|Ò|Õ|Ọ|Ô|Ố|Ồ|Ỗ|Ộ|Ơ|Ớ|Ờ|Ỡ|Ợ", "O", text)
        text = re.sub(r"ò|ó|ọ|ỏ|õ|ô|ồ|ố|ộ|ổ|ỗ|ơ|ờ|ớ|ợ|ở|ỡ", "o", text)
        text = re.sub(r"U|Ú|Ù|Ũ|Ụ|Ư|Ứ|Ừ|Ữ|Ự", "U", text)
        text = re.sub(r"ù|ú|ụ|ủ|ũ|ư|ừ|ứ|ự|ử|ữ", "u", text)
        text = re.sub(r"Y|Ý|Ỳ|Ỹ|Ỵ", "Y", text)
        text = re.sub(r"ỳ|ý|ỵ|ỷ|ỹ", "y", text)
        text = re.sub(r"Đ", "D", text)
        text = re.sub(r"đ", "d", text)
        text = re.sub(
            r"\u0300|\u0301|\u0303|\u0309|\u0323", "", text
        )  # Huyền sắc hỏi ngã nặng
        text = re.sub(r"\u02C6|\u0306|\u031B", "", text)  # Â, Ê, Ă, Ơ, Ư
        return text

    def to_snake_case(text: str):
        return re.sub(r"(?<!^)(?=[A-Z])", "_", text).lower()

    def translate(sentence: str, lookup: dict[str, str], split_by=r"\W"):
        words = re.split(f"({split_by})", sentence)
        return "".join([lookup.get(w, w) for w in words])
