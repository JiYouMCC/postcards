import csv
from datetime import datetime


def parse_date(date_string):
    date_formats = [
        # 2/Nov/2019
        '%d/%b/%Y',
        # 20-Dec-21
        '%d-%b-%y',
        # 4/10/2020 0:18
        '%m/%d/%Y %H:%M',
        # 2025-07-07 14:21:15
        '%Y-%m-%d %H:%M:%S',
        # 2025-12-09 07:53
        '%Y-%m-%d %H:%M',
        # 2025-12-14 19:46:59 +08:00
        '%Y-%m-%d %H:%M:%S %z',
        # 6/26/2021
        '%m/%d/%Y',
    ]

    for date_format in date_formats:
        try:
            return datetime.strptime(date_string, date_format)
        except ValueError:
            continue

    return None


for mode in [0, 1]:
    if mode == 0:
        file_path = "../_data/received.csv"
    else:
        file_path = "../_data/sent.csv"
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        data = list(reader)

    for row in data:
        row['parsed_date'] = parse_date(
            row['received_date' if mode == 0 else 'sent_date'])

    sorted_data = sorted(
        [row for row in data if row['parsed_date'] is not None],
        key=lambda x: x['parsed_date']
    )

    with open(file_path, mode='w', encoding='utf-8', newline='') as file:
        fieldnames = reader.fieldnames
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in sorted_data:
            writer.writerow({key: row[key] for key in fieldnames})

    print(f"File {file_path} has been sorted and updated.")
