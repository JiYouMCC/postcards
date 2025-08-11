from bs4 import BeautifulSoup
import requests
import time
import csv


# received = 0
# sent = 1
mode = 0

exclude_list = ["CNSH42434"]

post_link_list = [["活动","/sendpostcard/postcardDetail/1320505","CNHN14819"],["活动","/sendpostcard/postcardDetail/1320501","CNGD68698"],["配对","/sendpostcard/postcardDetail/1320305","CNGD68682"],["配对","/sendpostcard/postcardDetail/1319259","CNHN14795"],["活动","/sendpostcard/postcardDetail/1318888","CNBJ43830"],["赠送","/sendpostcard/postcardDetail/1318763","CNHN14792"],["配对","/sendpostcard/postcardDetail/1318259","CNTJ15130"],["配对","/sendpostcard/postcardDetail/1317566","CNGD68329"],["配对","/sendpostcard/postcardDetail/1317553","CNFJ9705"],["配对","/sendpostcard/postcardDetail/1316958","CNTJ15065"],["配对","/sendpostcard/postcardDetail/1316126","CNSH41800"],["配对","/sendpostcard/postcardDetail/1315933","CNGD68031"],["活动","/sendpostcard/postcardDetail/1315692","CNGD68006"],["配对","/sendpostcard/postcardDetail/1315645","CNZJ29486"],["赠送","/sendpostcard/postcardDetail/1315359","CNBJ43537"],["配对","/sendpostcard/postcardDetail/1315241","CNTM70719"],["配对","/sendpostcard/postcardDetail/1313757","CNSH41470"],["配对","/sendpostcard/postcardDetail/1313615","CNGD67745"],["配对","/sendpostcard/postcardDetail/1313072","CNTJ14839"],["活动","/sendpostcard/postcardDetail/1312991","CNBJ43309"],["活动","/sendpostcard/postcardDetail/1312989","CNTM70514"],["活动","/sendpostcard/postcardDetail/1312843","CNHB6320"],["活动","/sendpostcard/postcardDetail/1312784","CNTM70499"],["活动","/sendpostcard/postcardDetail/1312779","CNJS26776"],["配对","/sendpostcard/postcardDetail/1311976","CNXZ0673"],["活动","/sendpostcard/postcardDetail/1311846","CNHB6275"],["活动","/sendpostcard/postcardDetail/1311550","CNJS26682"],["配对","/sendpostcard/postcardDetail/1310802","CNJS26615"],["配对","/sendpostcard/postcardDetail/1310215","CNGZ3565"],["活动","/sendpostcard/postcardDetail/1309462","CNZJ29227"],["配对","/sendpostcard/postcardDetail/1309012","CNHA5479"],["活动","/sendpostcard/postcardDetail/1308825","CNBJ42987"],["活动","/sendpostcard/postcardDetail/1308704","CNGD67242"],["活动","/sendpostcard/postcardDetail/1308389","CNHK0892"],["活动","/sendpostcard/postcardDetail/1308226","CNZJ29115"],["活动","/sendpostcard/postcardDetail/1308177","CNHE8978"],["活动","/sendpostcard/postcardDetail/1308164","CNZJ29112"],["活动","/sendpostcard/postcardDetail/1308157","CNTM70051"],["活动","/sendpostcard/postcardDetail/1307854","CNSH40631"],["活动","/sendpostcard/postcardDetail/1307852","CNTM70000"],["活动","/sendpostcard/postcardDetail/1307790","CNBJ42867"],["活动","/sendpostcard/postcardDetail/1307772","CNSC9108"],["活动","/sendpostcard/postcardDetail/1307754","CNTM69975"],["活动","/sendpostcard/postcardDetail/1307753","CNHK0876"],["配对","/sendpostcard/postcardDetail/1307481","CNHB6101"],["赠送","/sendpostcard/postcardDetail/1307363","CNHN14540"],["赠送","/sendpostcard/postcardDetail/1307341","CNLN10290"],["活动","/sendpostcard/postcardDetail/1307141","CNNM1646"],["配对","/sendpostcard/postcardDetail/1306823","CNTM69880"],["活动","/sendpostcard/postcardDetail/1306151","CNCQ10676"]]
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
    if url[2] in exclude_list:
        print("%s 编号在排除列表中，跳过"% url[2])
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
            if exists == False:
                print("编号不存在，写入目标文件")
                print("编号:", row_source[1])
                writer.writerow(row_source)
