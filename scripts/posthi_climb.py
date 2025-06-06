import csv

source_file_path = "../../_data/postcard/Post-Hi_已登记_收方向_20250526093033.csv"
target_file_path = "../../_data/postcard/received.csv"


with open(source_file_path, mode='r', newline='', encoding='utf-8') as source_file:
    with open(target_file_path, mode='r', newline='', encoding='utf-8') as target_file:
        with open(target_file_path, mode='a', newline='', encoding='utf-8') as target_file_write:
            reader_source = csv.reader(source_file)
            reader_target = csv.reader(target_file)
            reader_source = list(reader_source)
            reader_target = list(reader_target)
            writer = csv.writer(target_file_write)

            for row_source in reader_source:
                if reader_source.index(row_source) == 0:
                    continue
                for row_target in reader_target:
                    if row_source[0] == row_target[1]:
                        print("编号已存在，跳过")
                        break
                else:
                    # 如果没有相同的编号，则写入目标文件
                    print ("编号不存在，写入目标文件")
                    print ("编号:", row_source[0])
                    # no,id,title,type,platform,friend_id,country,region,sent_date,received_date,tags,url,friend_url
                    new_row = []
                    new_row.append("")
                    new_row.append(row_source[0])
                    new_row.append("")
                    new_row.append("MATCH" if row_source[1] == "匹配" else row_source[1])
                    new_row.append("Post-Hi")
                    new_row.append(row_source[5])
                    country = row_source[7].split(" ")[0]
                    if country == "中国":
                        country = "China"
                    new_row.append(country)
                    area = row_source[7].split(" ")[1]
                    if area.endswith("省") or area.endswith("市"):
                        area = area[:-1]
                    new_row.append(area)
                    new_row.append(row_source[9])
                    new_row.append(row_source[10])
                    new_row.append("")
                    new_row.append("https://www.post-hi.com/card/" + row_source[0])
                    new_row.append(row_source[6])
                    writer.writerow(new_row)

