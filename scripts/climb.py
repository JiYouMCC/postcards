from bs4 import BeautifulSoup
import requests
import time
import csv


# received = 0
# sent = 1
mode = 1

exclude_list = ["CNSH42434", "CNSH42824"]

post_link_list = [["配对","/sendpostcard/postcardDetail/1324082","CNSH43038"],["配对","/sendpostcard/postcardDetail/1323936","CNSH42946"],["配对","/sendpostcard/postcardDetail/1323864","CNSH42935"],["配对","/sendpostcard/postcardDetail/1323754","CNSH42921"],["配对","/sendpostcard/postcardDetail/1323655","CNSH42909"],["配对","/sendpostcard/postcardDetail/1323612","CNSH42894"],["配对","/sendpostcard/postcardDetail/1323490","CNSH42875"],["配对","/sendpostcard/postcardDetail/1323428","CNSH42866"],["配对","/sendpostcard/postcardDetail/1323207","CNSH42840"],["配对","/sendpostcard/postcardDetail/1323104","CNSH42825"],["配对","/sendpostcard/postcardDetail/1323103","CNSH42824"],["配对","/sendpostcard/postcardDetail/1323052","CNSH42820"],["配对","/sendpostcard/postcardDetail/1322923","CNSH42778"],["配对","/sendpostcard/postcardDetail/1322853","CNSH42772"],["配对","/sendpostcard/postcardDetail/1322752","CNSH42755"],["配对","/sendpostcard/postcardDetail/1322667","CNSH42733"],["配对","/sendpostcard/postcardDetail/1322521","CNSH42719"],["配对","/sendpostcard/postcardDetail/1322428","CNSH42692"],["配对","/sendpostcard/postcardDetail/1322304","CNSH42672"],["配对","/sendpostcard/postcardDetail/1322096","CNSH42646"],["配对","/sendpostcard/postcardDetail/1321334","CNSH42494"],["配对","/sendpostcard/postcardDetail/1321202","CNSH42470"],["配对","/sendpostcard/postcardDetail/1321051","CNSH42452"],["配对","/sendpostcard/postcardDetail/1320950","CNSH42435"],["配对","/sendpostcard/postcardDetail/1320949","CNSH42434"],["配对","/sendpostcard/postcardDetail/1320810","CNSH42423"],["配对","/sendpostcard/postcardDetail/1320743","CNSH42409"],["配对","/sendpostcard/postcardDetail/1320604","CNSH42392"],["配对","/sendpostcard/postcardDetail/1320510","CNSH42374"],["活动","/sendpostcard/postcardDetail/1320504","CNSH42372"],["活动","/sendpostcard/postcardDetail/1320502","CNSH42371"],["活动","/sendpostcard/postcardDetail/1320500","CNSH42370"],["配对","/sendpostcard/postcardDetail/1320352","CNSH42330"]]
requests.packages.urllib3.disable_warnings()
if mode == 0:
    target_file_path = "../_data/received.csv"
else:
    target_file_path = "../_data/sent.csv"

print('no,id,title,type,platform,friend_id,country,region,sent_date,received_date,tags,url,friend_url')

source_date = []
for url in post_link_list:
    response = requests.get("https://icardyou.icu"+url[1], verify=False)
    soup = BeautifulSoup(response.content, 'html.parser')

    new_line = []

    # 1. no = blank
    new_line.append("")
    print(',', end='')

    # 2. id
    new_line.append(url[2])
    print(url[2] + ',', end='')
    if url[2] in exclude_list:
        print("%s 编号在排除列表中，跳过" % url[2])
        continue

    # 3. title = blank
    new_line.append("")
    print(',', end='')

    # 4. type = url[0]
    card_type = url[0]
    if card_type == '配对':
        card_type = 'MATCH'
    new_line.append(card_type)
    print(card_type + ',', end='')

    # 5. platform = icardyou
    new_line.append('icardyou')
    print('icardyou,', end='')

    # 6. friend_id
    user_links = soup.find_all(
        'a', href=lambda href: href and href.startswith('/userInfo/homePage'))
    if user_links:
        new_line.append(user_links[mode].get_text(strip=True))
        print(user_links[mode].get_text(strip=True), end='')
    else:
        new_line.append("")
    print(',', end='')

    # 7. country = China
    new_line.append('China')
    print('China,', end='')

    # 8. region
    region_label = soup.find_all(
        'td', string=lambda string: string and "地区：" in string)
    if region_label:
        # Extract the region from the next td element
        region_value = region_label[mode].find_next('td').get_text(strip=True)
        new_line.append(region_value)
        print(region_value, end='')
    else:
        new_line.append("")
    print(',', end='')

    # 9. sent_date
    # Find the td element containing "发送时间："
    send_time_label = soup.find(
        'td', string=lambda string: string and "发送时间：" in string)
    if send_time_label:
        # Extract the date and time from the next td element
        send_time_value = send_time_label.find_next('td').get_text(strip=True)
        new_line.append(send_time_value)
        print(send_time_value, end='')
    else:
        new_line.append("")
    print(',', end='')

    # 10. received_date
    send_time_label = soup.find(
        'td', string=lambda string: string and "到达时间：" in string)
    if send_time_label:
        # Extract the date and time from the next td element
        send_time_value = send_time_label.find_next('td').get_text(strip=True)
        new_line.append(send_time_value)
        print(send_time_value, end='')
    else:
        new_line.append("")
    print(',', end='')

    # 11. tags = blank
    new_line.append("")
    print(',', end='')

    # 12. url = url[1]
    new_line.append("https://icardyou.icu"+url[1])
    print("https://icardyou.icu"+url[1]+',', end='')

    # 13. friend_url
    new_line.append("https://icardyou.icu"+user_links[mode]['href'])
    print("https://icardyou.icu"+user_links[mode]['href'])

    source_date.append(new_line)
    # sleep 10 sec
    time.sleep(2)

with open(target_file_path, mode='r', newline='', encoding='utf-8') as target_file:
    with open(target_file_path, mode='a', newline='', encoding='utf-8') as target_file_write:
        reader_target = csv.reader(target_file)
        reader_target = list(reader_target)
        writer = csv.writer(target_file_write)

        for row_source in source_date:
            exists = False
            for row_target in reader_target:
                if row_source[1] in row_target[1]:
                    print("编号已存在，跳过")
                    exists = True
                    break
            # 如果没有相同的编号，则写入目标文件
            if exists is False:
                print("编号不存在，写入目标文件")
                print("编号:", row_source[1])
                writer.writerow(row_source)
