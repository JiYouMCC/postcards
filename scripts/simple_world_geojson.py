import json

# 读取 world.geojson 文件
with open('world.geojson', 'r', encoding='utf-8') as file:
    data = json.load(file)

# 遍历 features，简化 properties
for feature in data.get('features', []):
    properties = feature.get('properties', {})
    feature['properties'] = {'SOVEREIGNT': properties.get('SOVEREIGNT')}

    # 简化几何数据，精度降低到小数点后4位
    def simplify_coordinates(coords):
        if isinstance(coords[0], list):
            return [simplify_coordinates(c) for c in coords]
        else:
            return [round(c, 4) for c in coords]
    geometry = feature.get('geometry', {})
    geometry_type = geometry.get('type')
    if geometry_type == 'Point':
        geometry['coordinates'] = simplify_coordinates(geometry['coordinates'])
    elif geometry_type in ['MultiPoint', 'LineString']:
        geometry['coordinates'] = simplify_coordinates(geometry['coordinates'])
    elif geometry_type in ['MultiLineString', 'Polygon']:
        geometry['coordinates'] = [simplify_coordinates(part) for part in geometry['coordinates']]
    elif geometry_type == 'MultiPolygon':
        geometry['coordinates'] = [[simplify_coordinates(part) for part in polygon] for polygon in geometry['coordinates']]
    feature['geometry'] = geometry

# 将简化后的数据写入新文件
with open('simplified_world.geojson', 'w', encoding='utf-8') as file:
    json.dump(data, file, separators=(',', ':'))

print("简化完成，结果已保存到 simplified_world.geojson 文件中。")
