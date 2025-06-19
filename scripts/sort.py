import csv
from datetime import datetime

# received = 0
# sent = 1
mode = 0

if mode == 0:
    file_path = "../_data/received.csv"
else:
    file_path = "../_data/sent.csv"

with open(file_path, mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    data = list(reader)


def parse_date(date_string):
    date_formats = [
        '%m/%d/%Y %H:%M',
        '%Y-%m-%d %H:%M:%S',
        '%d/%b/%Y',
        '%Y-%m-%d %H:%M',
        '%d-%b-%y'
    ]

    for date_format in date_formats:
        try:
            return datetime.strptime(date_string, date_format)
        except ValueError:
            continue

    return None


for row in data:
    row['parsed_date'] = parse_date(row['received_date' if mode == 0 else 'sent_date'])

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
