from bs4 import BeautifulSoup
import requests
import time
import csv


# received
#mode = 0
# sent
mode = 1

post_link_list = [["配对","/sendpostcard/postcardDetail/1314399","CNSH41550"],["配对","/sendpostcard/postcardDetail/1314354","CNSH41533"],["配对","/sendpostcard/postcardDetail/1314035","CNSH41515"],["配对","/sendpostcard/postcardDetail/1313958","CNSH41494"],["配对","/sendpostcard/postcardDetail/1313715","CNSH41465"],["配对","/sendpostcard/postcardDetail/1313708","CNSH41464"],["配对","/sendpostcard/postcardDetail/1313438","CNSH41418"],["活动","/sendpostcard/postcardDetail/1312990","CNSH41362"],["活动","/sendpostcard/postcardDetail/1312988","CNSH41361"],["配对","/sendpostcard/postcardDetail/1312886","CNSH41352"],["活动","/sendpostcard/postcardDetail/1312842","CNSH41340"],["活动","/sendpostcard/postcardDetail/1312783","CNSH41337"],["活动","/sendpostcard/postcardDetail/1312778","CNSH41335"],["配对","/sendpostcard/postcardDetail/1312667","CNSH41316"],["配对","/sendpostcard/postcardDetail/1312318","CNSH41243"],["配对","/sendpostcard/postcardDetail/1312225","CNSH41237"],["配对","/sendpostcard/postcardDetail/1312137","CNSH41228"],["配对","/sendpostcard/postcardDetail/1312056","CNSH41217"],["活动","/sendpostcard/postcardDetail/1311845","CNSH41192"],["配对","/sendpostcard/postcardDetail/1311767","CNSH41174"],["配对","/sendpostcard/postcardDetail/1311662","CNSH41164"],["活动","/sendpostcard/postcardDetail/1311549","CNSH41149"],["配对","/sendpostcard/postcardDetail/1311531","CNSH41146"],["配对","/sendpostcard/postcardDetail/1311427","CNSH41110"],["配对","/sendpostcard/postcardDetail/1311268","CNSH41076"],["配对","/sendpostcard/postcardDetail/1311162","CNSH41062"],["配对","/sendpostcard/postcardDetail/1311065","CNSH41053"],["配对","/sendpostcard/postcardDetail/1310921","CNSH41043"],["配对","/sendpostcard/postcardDetail/1310839","CNSH41003"],["配对","/sendpostcard/postcardDetail/1310814","CNSH41000"],["配对","/sendpostcard/postcardDetail/1310488","CNSH40961"],["配对","/sendpostcard/postcardDetail/1310390","CNSH40941"],["配对","/sendpostcard/postcardDetail/1310255","CNSH40933"],["配对","/sendpostcard/postcardDetail/1310171","CNSH40923"],["配对","/sendpostcard/postcardDetail/1310096","CNSH40919"],["配对","/sendpostcard/postcardDetail/1309989","CNSH40917"]]
# ignore warnings
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
    time.sleep(5)

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
            if exists == False:
                print("编号不存在，写入目标文件")
                print("编号:", row_source[1])
                writer.writerow(row_source)
