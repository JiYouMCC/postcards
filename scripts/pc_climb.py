from bs4 import BeautifulSoup
from date_format import parse_date, format_date
import csv
import requests
import time
from datetime import datetime, timezone, timedelta

exclude_list = []

sent_link = ["CN-4244187",
"CN-4243901",
"CN-4243900",
"CN-4243899",
"CN-4243122",
"CN-4241953",
"CN-4241441",
"CN-4230149",
"CN-4223322",
"CN-4221182",
"CN-4216224",
"CN-4215688",
"CN-4214649",
"CN-4212019",
"CN-4210326",
"CN-4208158",
"CN-4204865",
"CN-4203530",
"CN-4202755",
"CN-4201133",
"CN-4199183",
"CN-4197555",
"CN-4196794",
"CN-4196263",
"CN-4195967",
"CN-3531478",
"CN-3422089",
"CN-3384434",
"CN-3286898",
"CN-3280634",
"CN-3231348",
"CN-3228020",
"CN-3227813",
"CN-3226911",
"CN-3225353",
"CN-3225346",
"CN-3222983",
"CN-3217106",
"CN-3215716",
"CN-3210716",
"CN-3210715",
"CN-3198466",
"CN-3195165",
"CN-3195124",
"CN-3190759",
"CN-3188995",
"CN-3188921",
"CN-3187142",
"CN-3186987",
"CN-3178351",
"CN-3175553",
"CN-3174828",
"CN-3171383",
"CN-3169812",
"CN-3162950",
"CN-3159658",
"CN-3158118",
"CN-3156991",
"CN-3153779",
"CN-3152073",
"CN-3150883",
"CN-3150770",
"CN-3150768",
"CN-3147583",
"CN-3143489",
"CN-3142971",
"CN-3141900",
"CN-3132323",
"CN-3132322",
"CN-3132321",
"CN-3132319",
"CN-3132318",
"CN-3118825",
"CN-3118823",
"CN-3118822",
"CN-3112061",
"CN-3108962",
"CN-3108961",
"CN-3108960",
"CN-3107981",
"CN-3107474",
"CN-3101924",
"CN-3091116",
"CN-3089407",
"CN-3082666",
"CN-3080975",
"CN-3080281",
"CN-3075465",
"CN-3072608",
"CN-3072605",
"CN-3072603",
"CN-3067164",
"CN-3066911",
"CN-3064514",
"CN-3053297",
"CN-3053296",
"CN-3053163",
"CN-3047658",
"CN-3047343",
"CN-3044241",
"CN-3044240",
"CN-3042682",
"CN-3037787",
"CN-3036906",
"CN-3034159",
"CN-3033208",
"CN-3027129",
"CN-3024318",
"CN-3015949",
"CN-3015509",
"CN-3012577",
"CN-3012003",
"CN-3011370",
"CN-3007699",
"CN-3002361",
"CN-2995276",
"CN-2995272",
"CN-2991557",
"CN-2991499",
"CN-2984305",
"CN-2984303",
"CN-2981454",
"CN-2976144",
"CN-2975051",
"CN-2973293",
"CN-2973018",
"CN-2972021",
"CN-2968529",
"CN-2968528",
"CN-2968527",
"CN-2962157",
"CN-2962156",
"CN-2962155",
"CN-2961395",
"CN-2960806",
"CN-2958416",
"CN-2955254",
"CN-2954845",
"CN-2952127",
"CN-2945500",
"CN-2945499",
"CN-2941615",
"CN-2941156",
"CN-2940010",
"CN-2937661",
"CN-2933872",
"CN-2933437",
"CN-2932826",
"CN-2932825",
"CN-2931712",
"CN-2925755",
"CN-2868396",
"CN-2850381",
"CN-2845197",
"CN-2839745",
"CN-2839744",
"CN-2839451",
"CN-2839747",
"CN-2839701",
"CN-2894828",
"CN-2887120",
"CN-2883881",
"CN-2882373",
"CN-2882372",
"CN-2882371",
"CN-2869128",
"CN-2908462",
"CN-2906270",
"CN-2901559",
"CN-2899983",
"CN-2899945",
"CN-2899850",
"CN-2895464",
"CN-2914852",
"CN-2913881",
"CN-2910424",
"CN-2910423",
"CN-2926520",
"CN-2925759",
"CN-2925758",
"CN-2925757",
"CN-2925756",
"CN-2925754"]

received_lint = []

requests.packages.urllib3.disable_warnings()


def process(mode, post_link_list):
    if mode == 0:
        target_file_path = "../_data/received.csv"
    else:
        target_file_path = "../_data/sent.csv"

    processed_link_list = post_link_list

    # 预处理
    with open(target_file_path, mode='r', newline='', encoding='utf-8') as target_file:
        reader_target = csv.reader(target_file)
        reader_target = list(reader_target)

        for row_target in reader_target:
            for link in post_link_list:
                if row_target[1] == link:
                    processed_link_list.remove(link)
                    print("编号已存在，跳过:", row_target[1])
                    break

    print('no,id,title,type,platform,friend_id,country,region,sent_date,received_date,tags,url,friend_url')

    source_date = []
    for postcard_id in processed_link_list:
        print (postcard_id)
        continue
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

        # 8. region
        if mode == 0:
            sender_region = soup.find('div', class_='details-box sender').find('a', attrs={'itemprop': 'addressCountry'}).get('title').split(',')[0]
            region = sender_region
        else:
            receiver_region = soup.find('div', class_='details-box receiver right').find('a', attrs={'itemprop': 'addressCountry'}).get('title').split(',')[0]
            region = receiver_region
        if country == "Taiwan":
            country = "China"
            region = "台湾"

        new_line.append(country)
        print(country + ',', end='')
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
