from bs4 import BeautifulSoup
import requests
import time
import csv
post_link_list = [["活动", "/sendpostcard/postcardDetail/1309462", "CNZJ29227"]]
# ignore warnings
requests.packages.urllib3.disable_warnings()
target_file_path = "../../_data/postcard/received.csv"

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
    new_line.append(url[0])
    print(url[0] + ',', end='')

    # 5. platform = icardyou
    new_line.append('icardyou')
    print('icardyou,', end='')

    # 6. friend_id
    user_links = soup.find_all(
        'a', href=lambda href: href and href.startswith('/userInfo/homePage'))
    if user_links:
        new_line.append(user_links[0].get_text(strip=True))
        print(user_links[0].get_text(strip=True), end='')
    else:
        new_line.append("")
    print(',', end='')

    # 7. country = China
    new_line.append('China')
    print('China,', end='')

    # 8. region
    region_label = soup.find(
        'td', string=lambda string: string and "地区：" in string)
    if region_label:
        # Extract the region from the next td element
        region_value = region_label.find_next('td').get_text(strip=True)
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
    new_line.append("https://icardyou.icu"+user_links[0]['href'])
    print("https://icardyou.icu"+user_links[0]['href'])

    source_date.append(new_line)
    # sleep 10 sec
    time.sleep(10)

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
