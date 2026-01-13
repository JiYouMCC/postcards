from bs4 import BeautifulSoup
from date_format import parse_date, format_date
import csv
import requests
import time

exclude_list = ["CNSH42434", "CNSH42824", "CNHE2329"]

sent_link_list = [["配对","/sendpostcard/postcardDetail/1333432","CNSH44334"],["配对","/sendpostcard/postcardDetail/1333313","CNSH44324"],["配对","/sendpostcard/postcardDetail/1333130","CNSH44279"],["配对","/sendpostcard/postcardDetail/1332688","CNSH44232"],["配对","/sendpostcard/postcardDetail/1332687","CNSH44231"],["配对","/sendpostcard/postcardDetail/1332613","CNSH44223"],["配对","/sendpostcard/postcardDetail/1332331","CNSH44185"],["配对","/sendpostcard/postcardDetail/1332157","CNSH44163"],["配对","/sendpostcard/postcardDetail/1332106","CNSH44157"],["配对","/sendpostcard/postcardDetail/1331632","CNSH44110"],["配对","/sendpostcard/postcardDetail/1331629","CNSH44109"],["配对","/sendpostcard/postcardDetail/1331628","CNSH44108"],["配对","/sendpostcard/postcardDetail/1331627","CNSH44107"],["配对","/sendpostcard/postcardDetail/1331626","CNSH44106"],["配对","/sendpostcard/postcardDetail/1331619","CNSH44105"],["配对","/sendpostcard/postcardDetail/1331539","CNSH44094"],["配对","/sendpostcard/postcardDetail/1331468","CNSH44085"],["配对","/sendpostcard/postcardDetail/1331382","CNSH44072"],["配对","/sendpostcard/postcardDetail/1331311","CNSH44067"],["配对","/sendpostcard/postcardDetail/1331219","CNSH44059"],["配对","/sendpostcard/postcardDetail/1331162","CNSH44049"],["配对","/sendpostcard/postcardDetail/1331004","CNSH44021"],["配对","/sendpostcard/postcardDetail/1330938","CNSH44012"],["配对","/sendpostcard/postcardDetail/1330832","CNSH44002"],["配对","/sendpostcard/postcardDetail/1330733","CNSH43994"],["配对","/sendpostcard/postcardDetail/1330635","CNSH43989"],["配对","/sendpostcard/postcardDetail/1330484","CNSH43982"],["配对","/sendpostcard/postcardDetail/1330165","CNSH43917"],["配对","/sendpostcard/postcardDetail/1330016","CNSH43902"],["配对","/sendpostcard/postcardDetail/1329941","CNSH43884"],["配对","/sendpostcard/postcardDetail/1329863","CNSH43877"],["活动","/sendpostcard/postcardDetail/1329781","CNSH43864"]]
sent_link_list += [["活动","/sendpostcard/postcardDetail/1329779","CNSH43863"],["配对","/sendpostcard/postcardDetail/1329585","CNSH43857"],["配对","/sendpostcard/postcardDetail/1329583","CNSH43855"],["配对","/sendpostcard/postcardDetail/1329517","CNSH43848"],["配对","/sendpostcard/postcardDetail/1329479","CNSH43836"],["配对","/sendpostcard/postcardDetail/1329401","CNSH43820"],["配对","/sendpostcard/postcardDetail/1329325","CNSH43810"],["配对","/sendpostcard/postcardDetail/1329293","CNSH43804"],["配对","/sendpostcard/postcardDetail/1329205","CNSH43790"],["配对","/sendpostcard/postcardDetail/1329142","CNSH43783"],["活动","/sendpostcard/postcardDetail/1329094","CNSH43777"],["活动","/sendpostcard/postcardDetail/1329017","CNSH43760"],["配对","/sendpostcard/postcardDetail/1328995","CNSH43759"],["配对","/sendpostcard/postcardDetail/1328914","CNSH43748"],["配对","/sendpostcard/postcardDetail/1328779","CNSH43735"],["配对","/sendpostcard/postcardDetail/1328640","CNSH43708"],["配对","/sendpostcard/postcardDetail/1328542","CNSH43694"],["配对","/sendpostcard/postcardDetail/1328459","CNSH43679"],["配对","/sendpostcard/postcardDetail/1327491","CNSH43548"],["配对","/sendpostcard/postcardDetail/1327474","CNSH43544"],["配对","/sendpostcard/postcardDetail/1327473","CNSH43543"],["配对","/sendpostcard/postcardDetail/1327472","CNSH43542"],["配对","/sendpostcard/postcardDetail/1327471","CNSH43541"],["配对","/sendpostcard/postcardDetail/1327470","CNSH43540"],["配对","/sendpostcard/postcardDetail/1327469","CNSH43539"],["配对","/sendpostcard/postcardDetail/1327468","CNSH43538"],["配对","/sendpostcard/postcardDetail/1327466","CNSH43536"],["配对","/sendpostcard/postcardDetail/1327420","CNSH43524"],["配对","/sendpostcard/postcardDetail/1327176","CNSH43490"],["配对","/sendpostcard/postcardDetail/1327069","CNSH43466"],["配对","/sendpostcard/postcardDetail/1327018","CNSH43450"],["配对","/sendpostcard/postcardDetail/1326942","CNSH43439"],["配对","/sendpostcard/postcardDetail/1326928","CNSH43437"],["配对","/sendpostcard/postcardDetail/1326792","CNSH43410"],["配对","/sendpostcard/postcardDetail/1326725","CNSH43394"],["配对","/sendpostcard/postcardDetail/1326646","CNSH43380"],["配对","/sendpostcard/postcardDetail/1326587","CNSH43373"],["配对","/sendpostcard/postcardDetail/1326392","CNSH43346"],["配对","/sendpostcard/postcardDetail/1325940","CNSH43299"],["赠送","/sendpostcard/postcardDetail/1325256","CNSH43201"],["配对","/sendpostcard/postcardDetail/1325232","CNSH43199"],["配对","/sendpostcard/postcardDetail/1325231","CNSH43198"],["配对","/sendpostcard/postcardDetail/1325230","CNSH43197"],["配对","/sendpostcard/postcardDetail/1325229","CNSH43196"],["配对","/sendpostcard/postcardDetail/1325228","CNSH43195"],["配对","/sendpostcard/postcardDetail/1325227","CNSH43194"],["活动","/sendpostcard/postcardDetail/1324848","CNSH43153"]]


received_link_list = [["配对","/sendpostcard/postcardDetail/1333575","CNZJ30556"],["赠送","/sendpostcard/postcardDetail/1333532","CNTM72370"],["配对","/sendpostcard/postcardDetail/1332973","CNSH44262"],["配对","/sendpostcard/postcardDetail/1332970","CNGD69962"],["赠送","/sendpostcard/postcardDetail/1332690","CNTM72221"],["配对","/sendpostcard/postcardDetail/1332407","CNTM72196"],["配对","/sendpostcard/postcardDetail/1331831","CNSH44133"],["配对","/sendpostcard/postcardDetail/1331216","CNXJ0687"],["配对","/sendpostcard/postcardDetail/1330575","CNGD69717"],["赠送","/sendpostcard/postcardDetail/1330295","CNSD16021"],["活动","/sendpostcard/postcardDetail/1329782","CNTM71890"],["活动","/sendpostcard/postcardDetail/1329780","CNTJ15906"],["配对","/sendpostcard/postcardDetail/1329647","CNTM71867"],["配对","/sendpostcard/postcardDetail/1329519","CNSC9735"],["配对","/sendpostcard/postcardDetail/1329518","CNYN1946"],["活动","/sendpostcard/postcardDetail/1329095","CNTM71849"],["配对","/sendpostcard/postcardDetail/1329052","CNSN5547"],["活动","/sendpostcard/postcardDetail/1329018","CNTM71844"],["配对","/sendpostcard/postcardDetail/1328471","CNSH43680"],["配对","/sendpostcard/postcardDetail/1328206","CNBJ44541"],["赠送","/sendpostcard/postcardDetail/1328147","CNTW4201"],["配对","/sendpostcard/postcardDetail/1327437","CNSH43531"],["配对","/sendpostcard/postcardDetail/1327281","CNFJ9997"],["赠送","/sendpostcard/postcardDetail/1327012","CNZJ30167"],["赠送","/sendpostcard/postcardDetail/1326417","CNCQ11245"],["配对","/sendpostcard/postcardDetail/1325905","CNJS27822"],["配对","/sendpostcard/postcardDetail/1325822","CNSC9578"],["配对","/sendpostcard/postcardDetail/1325417","CNHB6666"],["配对","/sendpostcard/postcardDetail/1325413","FNEU0267"],["配对","/sendpostcard/postcardDetail/1325319","CNHB6656"],["活动","/sendpostcard/postcardDetail/1324849","CNBJ44219"],["配对","/sendpostcard/postcardDetail/1324645","CNSH43122"],["配对","/sendpostcard/postcardDetail/1324503","CNSC9534"],["配对","/sendpostcard/postcardDetail/1323296","CNLN10674"],["配对","/sendpostcard/postcardDetail/1322135","CNJX4322"],["活动","/sendpostcard/postcardDetail/1320505","CNHN14819"],["活动","/sendpostcard/postcardDetail/1320503","CNHE9150"],["活动","/sendpostcard/postcardDetail/1320501","CNGD68698"],["配对","/sendpostcard/postcardDetail/1320305","CNGD68682"],["配对","/sendpostcard/postcardDetail/1319259","CNHN14795"],["活动","/sendpostcard/postcardDetail/1318888","CNBJ43830"],["赠送","/sendpostcard/postcardDetail/1318763","CNHN14792"],["配对","/sendpostcard/postcardDetail/1318259","CNTJ15130"],["配对","/sendpostcard/postcardDetail/1318164","CNGD68507"],["配对","/sendpostcard/postcardDetail/1317566","CNGD68329"],["配对","/sendpostcard/postcardDetail/1317553","CNFJ9705"],["配对","/sendpostcard/postcardDetail/1316958","CNTJ15065"],["配对","/sendpostcard/postcardDetail/1316126","CNSH41800"],["配对","/sendpostcard/postcardDetail/1315933","CNGD68031"],["活动","/sendpostcard/postcardDetail/1315692","CNGD68006"]]

requests.packages.urllib3.disable_warnings()


def process(mode, post_link_list):
    if mode == 0:
        target_file_path = "../_data/received.csv"
    else:
        target_file_path = "../_data/sent.csv"

    print('no,id,title,type,platform,friend_id,country,region,sent_date,received_date,tags,url,friend_url')

    source_date = []
    for url in post_link_list:
        response = requests.get("https://icardyou.icu" + url[1], verify=False)
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
        if card_type == '回寄' or card_type == '赠送':
            card_type = 'GIVE'
        if card_type == '活动':
            card_type = 'GAME'
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
            send_time_value = parse_date(send_time_value)
            send_time_value = format_date(send_time_value)
            new_line.append(send_time_value)
            print(send_time_value, end='')
        else:
            new_line.append("")
        print(',', end='')

        # 10. received_date
        received_time_label = soup.find(
            'td', string=lambda string: string and "到达时间：" in string)
        if received_time_label:
            # Extract the date and time from the next td element
            received_time_value = received_time_label.find_next('td').get_text(strip=True)
            received_time_value = parse_date(received_time_value)
            received_time_value = format_date(received_time_value)
            new_line.append(received_time_value)
            print(received_time_value, end='')
        else:
            new_line.append("")
        print(',', end='')

        # 11. tags = blank
        new_line.append("")
        print(',', end='')

        # 12. url = url[1]
        new_line.append("https://icardyou.icu" + url[1])
        print("https://icardyou.icu" + url[1] + ',', end='')

        # 13. friend_url
        new_line.append("https://icardyou.icu" + user_links[mode]['href'])
        print("https://icardyou.icu" + user_links[mode]['href'])

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


process(0, received_link_list)
process(1, sent_link_list)
