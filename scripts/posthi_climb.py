import csv
import glob
import os
import re
from pathlib import Path
from date_format import parse_date, format_date


DEFAULT_EXCLUDE_LIST = {
    "PHCNGD-0767",
    "PHCNZJ-1410",
    "PHCNFJ-1299",
    "PHCNSH-1876",
    "PHCNSC-0865",
    "PHCNZJ-3796",
    "PHCNJX-0993",
    "PHCNGD-5164",
    "PHCNSX-0251",
    "PHCNSC-0417",
    "PHCNHL-0176",
    "PHCNSD-2913",
}

# kept for backward compat with old standalone code below
exclude_list = list(DEFAULT_EXCLUDE_LIST)


def get_latest_file(pattern):
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError("[Error] 找不到符合模式的文件: {}".format(pattern))
    return max(files, key=os.path.getctime)


# ---------------------------------------------------------------------------
# Row-building helpers (also imported by postcards_qt.py)
# ---------------------------------------------------------------------------

def normalize_posthi_country(country: str) -> str:
    mapping = {"中国": "China", "日本": "Japan", "马来西亚": "Malaysia"}
    return mapping.get(country, country)


def normalize_posthi_card_type(card_type: str) -> str:
    mapping = {"匹配": "MATCH", "社区活动": "GAME"}
    if card_type in mapping:
        return mapping[card_type]
    if card_type in ("回寄", "赠送", "寄片"):
        return "GIVE"
    return card_type


def normalize_posthi_region(region: str) -> str:
    suffixes = [
        "壮族自治区", "回族自治区", "维吾尔自治区",
        "特别行政区", "自治区", "省", "市",
    ]
    normalized = region
    for suffix in suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
            break
    return normalized


def parse_optional_formatted_date(raw_value: str, parse_date_fn, format_date_fn) -> str:
    raw = (raw_value or "").strip()
    if not raw:
        return ""
    pattern = r"(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/][A-Za-z]{3}[-/]\d{2,4}|\d{1,2}/\d{1,2}/\d{4})"
    if not re.search(pattern, raw):
        return ""
    parsed = parse_date_fn(raw)
    formatted = format_date_fn(parsed)
    return formatted if formatted else ""


def pick_first_formatted_date(candidates: list, parse_date_fn, format_date_fn) -> str:
    for candidate in candidates:
        formatted = parse_optional_formatted_date(candidate, parse_date_fn, format_date_fn)
        if formatted:
            return formatted
    return ""


def build_posthi_row(row_source: list, mode: int, parse_date_fn, format_date_fn, exclude_ids=None):
    """Build one output CSV row from a Post-Hi source row.

    mode: 0 = received, 1 = sent, 2 = expired sent
    Returns None if the row should be skipped.
    """
    if not row_source:
        return None
    card_id = row_source[0].strip().upper()
    effective_excludes = exclude_ids if exclude_ids is not None else DEFAULT_EXCLUDE_LIST
    if not card_id or card_id in effective_excludes:
        return None

    if mode == 2 and (len(row_source) < 2 or row_source[1].strip() != "已过期"):
        return None

    prefix = 1 if mode == 2 else 0

    def cell(idx: int) -> str:
        return row_source[idx].strip() if idx < len(row_source) else ""

    card_type = normalize_posthi_card_type(cell(1 + prefix))

    friend_id = cell(5 + prefix)
    friend_url = cell(6 + prefix)
    location = cell(7 + prefix)
    location_parts = location.split(" ", 1) if location else [""]
    country = normalize_posthi_country(location_parts[0].strip())
    region = normalize_posthi_region(location_parts[1].strip()) if len(location_parts) > 1 else ""

    if mode == 2:
        sent_date = pick_first_formatted_date([cell(15), cell(14), cell(13)], parse_date_fn, format_date_fn)
        received_date = ""
    else:
        sent_date = pick_first_formatted_date([cell(9), cell(8), cell(10)], parse_date_fn, format_date_fn)
        received_date = pick_first_formatted_date([cell(10), cell(11), cell(12)], parse_date_fn, format_date_fn)

    return [
        "",
        card_id,
        "",
        card_type,
        "Post-Hi",
        friend_id,
        country,
        region,
        sent_date,
        received_date,
        "",
        f"https://www.post-hi.com/card/{card_id}",
        friend_url,
    ]


def collect_posthi_rows(csv_path, mode: int, parse_date_fn, format_date_fn, exclude_ids=None) -> list:
    """Read a Post-Hi CSV export and return a list of output rows (skipping header)."""
    with open(csv_path, mode='r', newline='', encoding='utf-8') as f:
        rows = list(csv.reader(f))
    result = []
    for row in rows[1:]:
        built = build_posthi_row(row, mode, parse_date_fn, format_date_fn, exclude_ids)
        if built is not None:
            result.append(built)
    return result



if __name__ == "__main__":
    expired_sent_source_file_path = get_latest_file("../_data/Post-Hi_漂流中_寄方向_*.csv")
    sent_source_file_path = get_latest_file("../_data/Post-Hi_已登记_寄方向_*.csv")
    received_source_file_path = get_latest_file("../_data/Post-Hi_已登记_收方向_*.csv")

def process(mode, source_file_path):
    if mode == 0:
        target_file_path = "../_data/received.csv"
    else:
        target_file_path = "../_data/sent.csv"
    with open(source_file_path, mode='r', newline='', encoding='utf-8') as source_file:
        with open(target_file_path, mode='r', newline='', encoding='utf-8') as target_file:
            with open(target_file_path, mode='a', newline='', encoding='utf-8') as target_file_write:
                reader_source = csv.reader(source_file)
                reader_target = csv.reader(target_file)
                reader_source = list(reader_source)
                reader_target = list(reader_target)
                writer = csv.writer(target_file_write)

                for row_source in reader_source:
                    if mode == 2 and row_source[1] != "已过期":
                        print("不是过期寄出片，跳过")
                        continue
                    if mode == 2:
                        prefix = 1
                    else:
                        prefix = 0
                    if reader_source.index(row_source) == 0:
                        continue
                    for row_target in reader_target:
                        if row_source[0] == row_target[1] or row_target[1].startswith(row_source[0] + "-"):
                            print("编号已存在，跳过")
                            break
                        if row_source[0] in exclude_list:
                            print(row_source[0] + "编号在排除列表中，跳过")
                            break
                    else:
                        # 如果没有相同的编号，则写入目标文件
                        print("编号不存在，写入目标文件")
                        print("编号:", row_source[0])
                        # no,id,title,type,platform,friend_id,country,region,sent_date,received_date,tags,url,friend_url
                        new_row = []
                        new_row.append("")
                        new_row.append(row_source[0])
                        new_row.append("")
                        card_type = normalize_posthi_card_type(row_source[1 + prefix])
                        new_row.append(card_type)
                        new_row.append("Post-Hi")
                        new_row.append(row_source[5 + prefix])
                        country = normalize_posthi_country(row_source[7 + prefix].split(" ")[0])
                        new_row.append(country)
                        area = normalize_posthi_region(row_source[7 + prefix].split(" ")[1])
                        new_row.append(area)
                        if mode == 2:
                            new_row.append(format_date(parse_date(row_source[15])))
                            new_row.append("")
                        else:
                            if row_source[9] == "":
                                new_row.append(format_date(parse_date(row_source[8])))
                            else:
                                new_row.append(format_date(parse_date(row_source[9])))
                            new_row.append(format_date(parse_date(row_source[10])))
                        new_row.append("")
                        new_row.append("https://www.post-hi.com/card/" + row_source[0])
                        new_row.append(row_source[6 + prefix])
                        writer.writerow(new_row)


if __name__ == "__main__":
    process(0, received_source_file_path)
    process(1, sent_source_file_path)
    process(2, expired_sent_source_file_path)
