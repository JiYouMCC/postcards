import csv
from pathlib import Path
from date_format import parse_date
from zoneinfo import ZoneInfo


def generate_group(data_dir=None):
    """Write grouped.csv summarising daily received/sent counts.

    data_dir: path to the _data folder. Defaults to ../data relative to cwd,
              which is the correct value when running as a standalone script.
    """
    if data_dir is None:
        data_dir = Path("../_data")
    data_dir = Path(data_dir)

    file_received_path = data_dir / "received.csv"
    file_sent_path = data_dir / "sent.csv"
    file_grouped_path = data_dir / "grouped.csv"

    grouped_map = {}
    grouped_result = []

    with open(file_received_path, mode='r', encoding='utf-8') as file_received:
        data_received = list(csv.DictReader(file_received))

    with open(file_sent_path, mode='r', encoding='utf-8') as file_sent:
        data_sent = list(csv.DictReader(file_sent))

    for row in data_received:
        parsed_date = parse_date(row['received_date'])
        parsed_date = parsed_date.astimezone(ZoneInfo("Asia/Shanghai"))
        row['parsed_date'] = parsed_date.strftime("%Y-%m-%d")

    for row in data_sent:
        parsed_date = parse_date(row['sent_date'])
        parsed_date = parsed_date.astimezone(ZoneInfo("Asia/Shanghai"))
        row['parsed_date'] = parsed_date.strftime("%Y-%m-%d")

    for row in data_received:
        date = row["parsed_date"]
        if date in grouped_map:
            grouped_map[date]["received"] += 1
        else:
            grouped_map[date] = {"received": 1, "sent": 0}

    for row in data_sent:
        date = row["parsed_date"]
        if date in grouped_map:
            grouped_map[date]["sent"] += 1
        else:
            grouped_map[date] = {"received": 0, "sent": 1}

    for key in grouped_map.keys():
        grouped_result.append({
            "date": key,
            "received": grouped_map[key]["received"],
            "sent": grouped_map[key]["sent"]
        })

    with open(file_grouped_path, mode='w', encoding='utf-8', newline='') as file:
        fieldnames = ["date", "received", "sent"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in grouped_result:
            writer.writerow({key: row[key] for key in fieldnames})


if __name__ == "__main__":
    generate_group()
