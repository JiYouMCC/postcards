from bs4 import BeautifulSoup
import requests
import time
import csv


# received = 0
# sent = 1
mode = 1

post_link_list = [["配对","/sendpostcard/postcardDetail/1316748","CNSH41861"],["配对","/sendpostcard/postcardDetail/1316494","CNSH41846"],["配对","/sendpostcard/postcardDetail/1316414","CNSH41831"],["配对","/sendpostcard/postcardDetail/1316299","CNSH41816"],["配对","/sendpostcard/postcardDetail/1316212","CNSH41809"],["配对","/sendpostcard/postcardDetail/1316102","CNSH41798"],["配对","/sendpostcard/postcardDetail/1316039","CNSH41768"],["配对","/sendpostcard/postcardDetail/1315928","CNSH41751"],["配对","/sendpostcard/postcardDetail/1315741","CNSH41730"],["活动","/sendpostcard/postcardDetail/1315691","CNSH41721"],["配对","/sendpostcard/postcardDetail/1315610","CNSH41714"],["配对","/sendpostcard/postcardDetail/1315541","CNSH41706"],["配对","/sendpostcard/postcardDetail/1315417","CNSH41700"],["赠送","/sendpostcard/postcardDetail/1315337","CNSH41695"],["配对","/sendpostcard/postcardDetail/1315292","CNSH41693"],["配对","/sendpostcard/postcardDetail/1315210","CNSH41679"],["配对","/sendpostcard/postcardDetail/1315024","CNSH41641"],["配对","/sendpostcard/postcardDetail/1315019","CNSH41640"],["配对","/sendpostcard/postcardDetail/1314935","CNSH41632"],["配对","/sendpostcard/postcardDetail/1314853","CNSH41616"],["配对","/sendpostcard/postcardDetail/1314784","CNSH41604"],["配对","/sendpostcard/postcardDetail/1314670","CNSH41575"],["配对","/sendpostcard/postcardDetail/1314605","CNSH41567"],["配对","/sendpostcard/postcardDetail/1314399","CNSH41550"],["配对","/sendpostcard/postcardDetail/1314354","CNSH41533"],["配对","/sendpostcard/postcardDetail/1314199","CNSH41523"],["配对","/sendpostcard/postcardDetail/1314155","CNSH41520"],["配对","/sendpostcard/postcardDetail/1314035","CNSH41515"],["配对","/sendpostcard/postcardDetail/1313958","CNSH41494"],["配对","/sendpostcard/postcardDetail/1313715","CNSH41465"],["配对","/sendpostcard/postcardDetail/1313708","CNSH41464"],["配对","/sendpostcard/postcardDetail/1313438","CNSH41418"],["配对","/sendpostcard/postcardDetail/1313189","CNSH41394"],["配对","/sendpostcard/postcardDetail/1313041","CNSH41364"],["活动","/sendpostcard/postcardDetail/1312990","CNSH41362"],["活动","/sendpostcard/postcardDetail/1312988","CNSH41361"],["配对","/sendpostcard/postcardDetail/1312886","CNSH41352"],["活动","/sendpostcard/postcardDetail/1312842","CNSH41340"],["活动","/sendpostcard/postcardDetail/1312783","CNSH41337"],["配对","/sendpostcard/postcardDetail/1312781","CNSH41336"],["活动","/sendpostcard/postcardDetail/1312778","CNSH41335"]]
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
            if exists == False:
                print("编号不存在，写入目标文件")
                print("编号:", row_source[1])
                writer.writerow(row_source)
