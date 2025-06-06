from bs4 import BeautifulSoup
import requests
import time
import csv
post_link_list = [["配对","/sendpostcard/postcardDetail/1311976","CNXZ0673"],["活动","/sendpostcard/postcardDetail/1311846","CNHB6275"],["活动","/sendpostcard/postcardDetail/1311550","CNJS26682"],["配对","/sendpostcard/postcardDetail/1310802","CNJS26615"],["配对","/sendpostcard/postcardDetail/1310215","CNGZ3565"],["活动","/sendpostcard/postcardDetail/1309462","CNZJ29227"],["活动","/sendpostcard/postcardDetail/1308825","CNBJ42987"],["活动","/sendpostcard/postcardDetail/1308704","CNGD67242"],["活动","/sendpostcard/postcardDetail/1308389","CNHK0892"],["活动","/sendpostcard/postcardDetail/1308226","CNZJ29115"],["活动","/sendpostcard/postcardDetail/1308177","CNHE8978"],["活动","/sendpostcard/postcardDetail/1308164","CNZJ29112"],["活动","/sendpostcard/postcardDetail/1308157","CNTM70051"],["活动","/sendpostcard/postcardDetail/1307854","CNSH40631"],["活动","/sendpostcard/postcardDetail/1307852","CNTM70000"],["活动","/sendpostcard/postcardDetail/1307790","CNBJ42867"],["活动","/sendpostcard/postcardDetail/1307754","CNTM69975"],["活动","/sendpostcard/postcardDetail/1307753","CNHK0876"],["配对","/sendpostcard/postcardDetail/1307481","CNHB6101"],["赠送","/sendpostcard/postcardDetail/1307363","CNHN14540"],["赠送","/sendpostcard/postcardDetail/1307341","CNLN10290"],["配对","/sendpostcard/postcardDetail/1306823","CNTM69880"],["活动","/sendpostcard/postcardDetail/1306151","CNCQ10676"],["赠送","/sendpostcard/postcardDetail/1306121","CNTJ14399"],["活动","/sendpostcard/postcardDetail/1306067","CNGD67023"],["配对","/sendpostcard/postcardDetail/1305922","CNGX10175"],["活动","/sendpostcard/postcardDetail/1305872","CNGD67008"],["活动","/sendpostcard/postcardDetail/1305807","CNSN4943"],["活动","/sendpostcard/postcardDetail/1305713","CNTM69720"],["活动","/sendpostcard/postcardDetail/1305616","CNHE8958"],["配对","/sendpostcard/postcardDetail/1305545","CNJL2362"],["活动","/sendpostcard/postcardDetail/1305514","CNGD66984"],["活动","/sendpostcard/postcardDetail/1305414","CNZJ28993"],["活动","/sendpostcard/postcardDetail/1305397","CNSH40243"],["活动","/sendpostcard/postcardDetail/1304877","CNTJ14292"],["活动","/sendpostcard/postcardDetail/1304787","CNGD66904"],["活动","/sendpostcard/postcardDetail/1304710","CNCQ10633"],["活动","/sendpostcard/postcardDetail/1304684","CNHA5442"],["活动","/sendpostcard/postcardDetail/1304645","CNHK0787"],["活动","/sendpostcard/postcardDetail/1304624","CNTJ14269"],["活动","/sendpostcard/postcardDetail/1304601","CNLN10185"],["活动","/sendpostcard/postcardDetail/1304599","CNSH40130"],["活动","/sendpostcard/postcardDetail/1304595","CNZJ28945"],["活动","/sendpostcard/postcardDetail/1304593","CNNM1607"],["活动","/sendpostcard/postcardDetail/1304588","CNBJ42603"],["活动","/sendpostcard/postcardDetail/1303986","CNHK0762"],["配对","/sendpostcard/postcardDetail/1303952","CNSH40040"],["活动","/sendpostcard/postcardDetail/1303782","CNSD15544"],["活动","/sendpostcard/postcardDetail/1303645","CNSD15539"],["活动","/sendpostcard/postcardDetail/1302893","CNHE8898"]]
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
