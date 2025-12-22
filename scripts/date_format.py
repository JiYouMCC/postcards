import csv
from datetime import datetime, timezone, timedelta


def parse_date(date_string):
    """Parse a date string into a datetime object."""
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
            result = datetime.strptime(date_string, date_format)
            # add timezone if missing
            if result.tzinfo is None:
                return result.replace(tzinfo=timezone(timedelta(hours=8)))
            else:
                return result
        except ValueError:
            continue
    print (f"Failed to parse date: {date_string}")
    return None


def format_date(date_obj, tz_offset=timezone(timedelta(hours=8))):
    """ Format a datetime object into a standardized string."""
    if date_obj:
        if date_obj.tzinfo is None:
            date_obj = date_obj.replace(tzinfo=tz_offset)
        return date_obj.strftime('%Y-%m-%d %H:%M:%S %z')
    else:
        return None


def process_file(file_path, date_fields):
    """Process a CSV file to convert and sort date fields."""
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        data = list(reader)

    # Parse and format dates
    for row in data:
        for date_field in date_fields:
            if row[date_field]:  # Only process non-empty fields
                parsed_date = parse_date(row[date_field])
                row[date_field] = format_date(parsed_date)

    # Sort data by the first date field in the list
    # sorted_data = sorted(
    #     data,
    #     key=lambda x: parse_date(x[date_fields[0]]) if x[date_fields[0]] else datetime.min
    # )
    sorted_data=data

    # Write the updated data back to the file
    with open(file_path, mode='w', encoding='utf-8', newline='') as file:
        fieldnames = reader.fieldnames
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted_data)

    print(f"File {file_path} has been processed and updated.")


def main():
    # Process both received.csv and sent.csv
    process_file("../_data/received.csv", ["received_date", "sent_date"])
    process_file("../_data/sent.csv", ["received_date", "sent_date"])


if __name__ == "__main__":
    main()