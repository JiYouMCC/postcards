import csv
from datetime import datetime

file_received_path = "../_data/received.csv"
file_sent_path = "../_data/sent.csv"
file_grouped_path = "../_data/grouped.csv"

grouped_map = {}
grouped_result = []

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

with open(file_received_path, mode='r', encoding='utf-8') as file_received:
    file_received_reader = csv.DictReader(file_received)
    data_received = list(file_received_reader)

with open(file_sent_path, mode='r', encoding='utf-8') as file_sent:
    file_sent_reader = csv.DictReader(file_sent)
    data_sent = list(file_sent_reader)


for row in data_received:
    row['parsed_date'] = parse_date(row['received_date']).strftime("%Y-%m-%d")

for row in data_sent:
    row['parsed_date'] = parse_date(row['sent_date']).strftime("%Y-%m-%d")

for row in data_received:
    date = row["parsed_date"]
    if date in grouped_map:
        grouped_map[date]["received"] +=1
    else:
        grouped_map[date] = {
            "received" : 1,
            "sent" : 0
        }

for row in data_sent:
    date = row["parsed_date"]
    if date in grouped_map:
        grouped_map[date]["sent"] +=1
    else:
        grouped_map[date] = {
            "received" : 0,
            "sent" : 1
        }

for key in grouped_map.keys():
    grouped_result.append({
        "date":key,
        "received":grouped_map[key]["received"],
        "sent":grouped_map[key]["sent"]
    })


with open(file_grouped_path, mode='w', encoding='utf-8', newline='') as file:
    fieldnames = ["date","received","sent"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for row in grouped_result:
        writer.writerow({key: row[key] for key in fieldnames})