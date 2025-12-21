import csv
from datetime import datetime
from date_format import parse_date

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
