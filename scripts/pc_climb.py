from bs4 import BeautifulSoup
from date_format import parse_date, format_date
import csv
import requests
import time
from datetime import datetime, timezone, timedelta

exclude_list = []

sent_link = []

received_lint = []

requests.packages.urllib3.disable_warnings()


def process(mode, post_link_list):
    if mode == 0:
        target_file_path = "../_data/received.csv"
    else:
        target_file_path = "../_data/sent.csv"
    print('no,id,title,type,platform,friend_id,country,region,sent_date,received_date,tags,url,friend_url')

    source_date = []
    for postcard_id in post_link_list:
        response = requests.get("https://www.postcrossing.com/postcards/" + postcard_id, verify=False)
        soup = BeautifulSoup(response.content, 'html.parser')

        new_line = []

        # 1. no = blank
        new_line.append("")
        print(',', end='')

        # 2. id
        new_line.append(postcard_id)
        print(postcard_id + ',', end='')

        # 3. title = blank
        new_line.append("")
        print(',', end='')

        # 4. type = MATCH
        card_type = "MATCH"
        new_line.append(card_type)
        print(card_type + ',', end='')

        # 5. platform = POSTCROSSING
        platform = "POSTCROSSING"
        new_line.append(platform)
        print(platform + ',', end='')

        # 6. friend_id
        if mode == 0:
            sender = soup.find('div', class_='details-box sender').find('div', class_='h4').find('a', attrs={'itemprop': 'url'})
            if not sender is None:
                sender = sender.text.strip()
            else:
                sender = ""
            friend_id = sender
        else:
            receiver = soup.find('div', class_='details-box receiver right').find('div', class_='h4').find('a', attrs={'itemprop': 'url'})
            if not receiver is None:
                receiver = receiver.text.strip()
            else:
                receiver = ""
            friend_id = receiver
        new_line.append(friend_id)
        print(friend_id + ',', end='')

        # 7. country
        if mode == 0:
            sender_country = soup.find('div', class_='details-box sender').find('a', attrs={'itemprop': 'addressCountry'})
            if not sender_country is None:
                sender_country = sender_country.text.strip()
            else:
                sender_country = ""
            country = sender_country
        else:
            receiver_country = soup.find('div', class_='details-box receiver right').find('a', attrs={'itemprop': 'addressCountry'})
            if not receiver_country is None:
                receiver_country = receiver_country.text.strip()
            else:
                receiver_country = ""
            country = receiver_country
        new_line.append(country)
        print(country + ',', end='')

        # 8. region
        if mode == 0:
            sender_region = soup.find('div', class_='details-box sender').find('a', attrs={'itemprop': 'addressCountry'}).get('title').split(',')[0]
            region = sender_region
        else:
            receiver_region = soup.find('div', class_='details-box receiver right').find('a', attrs={'itemprop': 'addressCountry'}).get('title').split(',')[0]
            region = receiver_region
        new_line.append(region)
        print(region + ',', end='')

        # 9. sent_date
        sent_datetime = soup.find('div', class_='details-box sender').find('time').get('title')
        sent_datetime = sent_datetime.replace("Sent on ", "")
        sent_datetime = sent_datetime.replace(" (UTC)", "")
        sent_datetime = datetime.strptime(sent_datetime, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        new_line.append(format_date(sent_datetime))
        print(format_date(sent_datetime) + ',', end='')

        # 10. received_date
        receiver_datetime = soup.find('div', class_='details-box receiver right').find('time').get('title')
        receiver_datetime = receiver_datetime.replace("Received on ", "")
        receiver_datetime = receiver_datetime.replace(" (UTC)", "")
        receiver_datetime = datetime.strptime(receiver_datetime, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        new_line.append(format_date(receiver_datetime))
        print(format_date(receiver_datetime) + ',', end='')

        # 11. tags = blank
        new_line.append("")
        print(',', end='')

        # 12. url = https://www.postcrossing.com/postcards/ + postcard_id
        postcard_url = "https://www.postcrossing.com/postcards/" + postcard_id
        new_line.append(postcard_url)
        print(postcard_url + ',', end='')

        # 13. friend_url
        friend_url = "https://www.postcrossing.com/user/" + friend_id
        new_line.append(friend_url)
        print(friend_url)

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


process(1, sent_link)
process(0, received_lint)
