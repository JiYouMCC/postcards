import json

# 读取 world.geojson 文件
with open('world.geojson', 'r', encoding='utf-8') as file:
    data = json.load(file)

# 遍历 features，简化 properties
for feature in data.get('features', []):
    properties = feature.get('properties', {})
    feature['properties'] = {'SOVEREIGNT': properties.get('SOVEREIGNT')}

# 将简化后的数据写入新文件
with open('simplified_world.geojson', 'w', encoding='utf-8') as file:
    json.dump(data, file, separators=(',', ':'))

print("简化完成，结果已保存到 simplified_world.geojson 文件中。")
