import csv
from pathlib import Path
from date_format import parse_date


def sort_postcard_data(mode, data_dir=None):
    """Sort received.csv (mode=0) or sent.csv (mode=1) by date in place.

    data_dir: path to the _data folder. Defaults to ../data relative to cwd,
              which is the correct value when running as a standalone script.
    """
    if data_dir is None:
        data_dir = Path("../_data")
    data_dir = Path(data_dir)

    if mode == 0:
        file_path = data_dir / "received.csv"
    else:
        file_path = data_dir / "sent.csv"

    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        data = list(reader)
        fieldnames = reader.fieldnames

    for row in data:
        row['parsed_date'] = parse_date(
            row['received_date' if mode == 0 else 'sent_date'])

    sorted_data = sorted(
        [row for row in data if row['parsed_date'] is not None],
        key=lambda x: x['parsed_date']
    )

    with open(file_path, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in sorted_data:
            writer.writerow({key: row[key] for key in fieldnames})

    print(f"File {file_path} has been sorted and updated.")


if __name__ == "__main__":
    sort_postcard_data(0)
    sort_postcard_data(1)