from bs4 import BeautifulSoup
import requests
import time
import csv


exclude_list = ["CNSH42434", "CNSH42824"]

sent_link_list = [["配对","/sendpostcard/postcardDetail/1328640","CNSH43708"],["配对","/sendpostcard/postcardDetail/1327491","CNSH43548"],["配对","/sendpostcard/postcardDetail/1327473","CNSH43543"],["配对","/sendpostcard/postcardDetail/1327471","CNSH43541"],["配对","/sendpostcard/postcardDetail/1327468","CNSH43538"],["配对","/sendpostcard/postcardDetail/1327466","CNSH43536"],["配对","/sendpostcard/postcardDetail/1327420","CNSH43524"],["配对","/sendpostcard/postcardDetail/1327176","CNSH43490"],["配对","/sendpostcard/postcardDetail/1327069","CNSH43466"],["配对","/sendpostcard/postcardDetail/1327018","CNSH43450"],["配对","/sendpostcard/postcardDetail/1326942","CNSH43439"],["配对","/sendpostcard/postcardDetail/1326928","CNSH43437"],["配对","/sendpostcard/postcardDetail/1326792","CNSH43410"],["配对","/sendpostcard/postcardDetail/1326725","CNSH43394"],["配对","/sendpostcard/postcardDetail/1326646","CNSH43380"],["配对","/sendpostcard/postcardDetail/1326587","CNSH43373"],["配对","/sendpostcard/postcardDetail/1326392","CNSH43346"],["配对","/sendpostcard/postcardDetail/1325940","CNSH43299"],["赠送","/sendpostcard/postcardDetail/1325256","CNSH43201"],["配对","/sendpostcard/postcardDetail/1325232","CNSH43199"],["配对","/sendpostcard/postcardDetail/1325231","CNSH43198"],["配对","/sendpostcard/postcardDetail/1325230","CNSH43197"],["配对","/sendpostcard/postcardDetail/1325228","CNSH43195"],["配对","/sendpostcard/postcardDetail/1325227","CNSH43194"],["活动","/sendpostcard/postcardDetail/1324848","CNSH43153"],["配对","/sendpostcard/postcardDetail/1324805","CNSH43150"],["配对","/sendpostcard/postcardDetail/1324506","CNSH43101"],["配对","/sendpostcard/postcardDetail/1324505","CNSH43100"],["配对","/sendpostcard/postcardDetail/1324481","CNSH43096"],["配对","/sendpostcard/postcardDetail/1324480","CNSH43095"],["配对","/sendpostcard/postcardDetail/1324479","CNSH43094"],["配对","/sendpostcard/postcardDetail/1324478","CNSH43093"],["配对","/sendpostcard/postcardDetail/1324477","CNSH43092"],["配对","/sendpostcard/postcardDetail/1324476","CNSH43091"],["配对","/sendpostcard/postcardDetail/1324460","CNSH43087"],["配对","/sendpostcard/postcardDetail/1324291","CNSH43066"],["配对","/sendpostcard/postcardDetail/1324252","CNSH43063"],["配对","/sendpostcard/postcardDetail/1324237","CNSH43061"],["配对","/sendpostcard/postcardDetail/1324082","CNSH43038"],["配对","/sendpostcard/postcardDetail/1323936","CNSH42946"],["配对","/sendpostcard/postcardDetail/1323864","CNSH42935"],["配对","/sendpostcard/postcardDetail/1323754","CNSH42921"],["配对","/sendpostcard/postcardDetail/1323655","CNSH42909"],["配对","/sendpostcard/postcardDetail/1323612","CNSH42894"],["配对","/sendpostcard/postcardDetail/1323565","CNSH42886"],["配对","/sendpostcard/postcardDetail/1323490","CNSH42875"],["配对","/sendpostcard/postcardDetail/1323428","CNSH42866"],["配对","/sendpostcard/postcardDetail/1323207","CNSH42840"],["配对","/sendpostcard/postcardDetail/1323104","CNSH42825"],["配对","/sendpostcard/postcardDetail/1323103","CNSH42824"],["配对","/sendpostcard/postcardDetail/1323052","CNSH42820"],["配对","/sendpostcard/postcardDetail/1322923","CNSH42778"],["配对","/sendpostcard/postcardDetail/1322853","CNSH42772"],["配对","/sendpostcard/postcardDetail/1322752","CNSH42755"],["配对","/sendpostcard/postcardDetail/1322667","CNSH42733"],["配对","/sendpostcard/postcardDetail/1322521","CNSH42719"],["配对","/sendpostcard/postcardDetail/1322428","CNSH42692"],["配对","/sendpostcard/postcardDetail/1322304","CNSH42672"],["配对","/sendpostcard/postcardDetail/1322096","CNSH42646"],["配对","/sendpostcard/postcardDetail/1321334","CNSH42494"],["配对","/sendpostcard/postcardDetail/1321202","CNSH42470"],["配对","/sendpostcard/postcardDetail/1321051","CNSH42452"],["配对","/sendpostcard/postcardDetail/1320950","CNSH42435"],["配对","/sendpostcard/postcardDetail/1320949","CNSH42434"],["配对","/sendpostcard/postcardDetail/1320810","CNSH42423"],["配对","/sendpostcard/postcardDetail/1320743","CNSH42409"],["配对","/sendpostcard/postcardDetail/1320604","CNSH42392"],["配对","/sendpostcard/postcardDetail/1320510","CNSH42374"],["活动","/sendpostcard/postcardDetail/1320504","CNSH42372"],["活动","/sendpostcard/postcardDetail/1320502","CNSH42371"],["活动","/sendpostcard/postcardDetail/1320500","CNSH42370"],["配对","/sendpostcard/postcardDetail/1320352","CNSH42330"],["配对","/sendpostcard/postcardDetail/1320256","CNSH42316"],["配对","/sendpostcard/postcardDetail/1320106","CNSH42299"],["配对","/sendpostcard/postcardDetail/1320026","CNSH42288"],["配对","/sendpostcard/postcardDetail/1319951","CNSH42268"],["配对","/sendpostcard/postcardDetail/1319858","CNSH42256"],["配对","/sendpostcard/postcardDetail/1319739","CNSH42236"],["配对","/sendpostcard/postcardDetail/1319639","CNSH42219"],["配对","/sendpostcard/postcardDetail/1319484","CNSH42203"],["配对","/sendpostcard/postcardDetail/1319388","CNSH42183"],["配对","/sendpostcard/postcardDetail/1319306","CNSH42171"],["配对","/sendpostcard/postcardDetail/1319146","CNSH42152"],["配对","/sendpostcard/postcardDetail/1319069","CNSH42138"],["活动","/sendpostcard/postcardDetail/1318889","CNSH42115"],["配对","/sendpostcard/postcardDetail/1318838","CNSH42106"],["配对","/sendpostcard/postcardDetail/1318743","CNSH42093"],["配对","/sendpostcard/postcardDetail/1318567","CNSH42074"],["配对","/sendpostcard/postcardDetail/1318466","CNSH42053"],["配对","/sendpostcard/postcardDetail/1318349","CNSH42033"],["配对","/sendpostcard/postcardDetail/1318243","CNSH42019"],["配对","/sendpostcard/postcardDetail/1318156","CNSH41995"],["配对","/sendpostcard/postcardDetail/1317686","CNSH41982"],["配对","/sendpostcard/postcardDetail/1317529","CNSH41972"],["配对","/sendpostcard/postcardDetail/1317435","CNSH41947"],["配对","/sendpostcard/postcardDetail/1317221","CNSH41894"],["配对","/sendpostcard/postcardDetail/1317181","CNSH41892"],["配对","/sendpostcard/postcardDetail/1316996","CNSH41875"],["配对","/sendpostcard/postcardDetail/1316903","CNSH41867"],["配对","/sendpostcard/postcardDetail/1316812","CNSH41865"],["配对","/sendpostcard/postcardDetail/1316748","CNSH41861"],["配对","/sendpostcard/postcardDetail/1316494","CNSH41846"],["配对","/sendpostcard/postcardDetail/1316414","CNSH41831"],["配对","/sendpostcard/postcardDetail/1316299","CNSH41816"],["配对","/sendpostcard/postcardDetail/1316212","CNSH41809"],["配对","/sendpostcard/postcardDetail/1316102","CNSH41798"],["配对","/sendpostcard/postcardDetail/1316039","CNSH41768"],["配对","/sendpostcard/postcardDetail/1315928","CNSH41751"],["配对","/sendpostcard/postcardDetail/1315741","CNSH41730"],["活动","/sendpostcard/postcardDetail/1315691","CNSH41721"],["配对","/sendpostcard/postcardDetail/1315663","CNSH41720"],["配对","/sendpostcard/postcardDetail/1315610","CNSH41714"],["配对","/sendpostcard/postcardDetail/1315541","CNSH41706"],["配对","/sendpostcard/postcardDetail/1315417","CNSH41700"],["赠送","/sendpostcard/postcardDetail/1315337","CNSH41695"],["配对","/sendpostcard/postcardDetail/1315292","CNSH41693"],["配对","/sendpostcard/postcardDetail/1315210","CNSH41679"],["配对","/sendpostcard/postcardDetail/1315024","CNSH41641"],["配对","/sendpostcard/postcardDetail/1315019","CNSH41640"],["配对","/sendpostcard/postcardDetail/1314935","CNSH41632"],["配对","/sendpostcard/postcardDetail/1314853","CNSH41616"],["配对","/sendpostcard/postcardDetail/1314784","CNSH41604"],["配对","/sendpostcard/postcardDetail/1314670","CNSH41575"],["配对","/sendpostcard/postcardDetail/1314605","CNSH41567"],["配对","/sendpostcard/postcardDetail/1314399","CNSH41550"],["配对","/sendpostcard/postcardDetail/1314354","CNSH41533"],["配对","/sendpostcard/postcardDetail/1314199","CNSH41523"],["配对","/sendpostcard/postcardDetail/1314155","CNSH41520"],["配对","/sendpostcard/postcardDetail/1314035","CNSH41515"],["配对","/sendpostcard/postcardDetail/1313958","CNSH41494"],["配对","/sendpostcard/postcardDetail/1313715","CNSH41465"],["配对","/sendpostcard/postcardDetail/1313708","CNSH41464"]]

received_link_list = [["配对","/sendpostcard/postcardDetail/1328471","CNSH43680"],["配对","/sendpostcard/postcardDetail/1328206","CNBJ44541"],["配对","/sendpostcard/postcardDetail/1327437","CNSH43531"],["配对","/sendpostcard/postcardDetail/1327281","CNFJ9997"],["赠送","/sendpostcard/postcardDetail/1327012","CNZJ30167"],["赠送","/sendpostcard/postcardDetail/1326417","CNCQ11245"],["配对","/sendpostcard/postcardDetail/1325905","CNJS27822"],["配对","/sendpostcard/postcardDetail/1325822","CNSC9578"],["配对","/sendpostcard/postcardDetail/1325417","CNHB6666"],["配对","/sendpostcard/postcardDetail/1325413","FNEU0267"],["配对","/sendpostcard/postcardDetail/1325319","CNHB6656"],["活动","/sendpostcard/postcardDetail/1324849","CNBJ44219"],["配对","/sendpostcard/postcardDetail/1324645","CNSH43122"],["配对","/sendpostcard/postcardDetail/1324503","CNSC9534"],["配对","/sendpostcard/postcardDetail/1323296","CNLN10674"],["配对","/sendpostcard/postcardDetail/1322135","CNJX4322"],["活动","/sendpostcard/postcardDetail/1320505","CNHN14819"],["活动","/sendpostcard/postcardDetail/1320503","CNHE9150"],["活动","/sendpostcard/postcardDetail/1320501","CNGD68698"],["配对","/sendpostcard/postcardDetail/1320305","CNGD68682"],["配对","/sendpostcard/postcardDetail/1319259","CNHN14795"],["活动","/sendpostcard/postcardDetail/1318888","CNBJ43830"],["赠送","/sendpostcard/postcardDetail/1318763","CNHN14792"],["配对","/sendpostcard/postcardDetail/1318259","CNTJ15130"],["配对","/sendpostcard/postcardDetail/1318164","CNGD68507"],["配对","/sendpostcard/postcardDetail/1317566","CNGD68329"],["配对","/sendpostcard/postcardDetail/1317553","CNFJ9705"],["配对","/sendpostcard/postcardDetail/1316958","CNTJ15065"],["配对","/sendpostcard/postcardDetail/1316126","CNSH41800"],["配对","/sendpostcard/postcardDetail/1315933","CNGD68031"],["活动","/sendpostcard/postcardDetail/1315692","CNGD68006"],["配对","/sendpostcard/postcardDetail/1315645","CNZJ29486"],["赠送","/sendpostcard/postcardDetail/1315359","CNBJ43537"],["配对","/sendpostcard/postcardDetail/1315241","CNTM70719"],["配对","/sendpostcard/postcardDetail/1313757","CNSH41470"],["配对","/sendpostcard/postcardDetail/1313615","CNGD67745"],["配对","/sendpostcard/postcardDetail/1313072","CNTJ14839"],["活动","/sendpostcard/postcardDetail/1312991","CNBJ43309"],["活动","/sendpostcard/postcardDetail/1312989","CNTM70514"],["活动","/sendpostcard/postcardDetail/1312843","CNHB6320"],["活动","/sendpostcard/postcardDetail/1312784","CNTM70499"],["活动","/sendpostcard/postcardDetail/1312779","CNJS26776"],["配对","/sendpostcard/postcardDetail/1311976","CNXZ0673"],["活动","/sendpostcard/postcardDetail/1311846","CNHB6275"],["活动","/sendpostcard/postcardDetail/1311550","CNJS26682"],["配对","/sendpostcard/postcardDetail/1310802","CNJS26615"],["配对","/sendpostcard/postcardDetail/1310215","CNGZ3565"],["活动","/sendpostcard/postcardDetail/1309462","CNZJ29227"],["配对","/sendpostcard/postcardDetail/1309012","CNHA5479"],["活动","/sendpostcard/postcardDetail/1308825","CNBJ42987"]]

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
