import os
import glob
from PIL import Image

TARGET_WIDTH = 600


def resize_image(image_path, output_path):

    with Image.open(image_path) as image:
        width, height = image.size
        if width > height:
            target_width = TARGET_WIDTH
            target_height = int(height / width * TARGET_WIDTH)
        else:
            target_height = TARGET_WIDTH
            target_width = int(width / height * TARGET_WIDTH)
        resized_image = image.resize((target_width, target_height))
        resized_image.save(output_path)
        print(image_path)


folder_path = "."
result_folder_path = "results"
if not os.path.exists(result_folder_path):
    os.makedirs(result_folder_path)
image_formats = ['*.jpg', '*.jpeg', '*.png', '*.gif']
image_list = []
for image_format in image_formats:
    image_list.extend(glob.glob(os.path.join(folder_path, image_format)))
for image_path in image_list:
    resize_image(image_path, os.path.join(result_folder_path, image_path))