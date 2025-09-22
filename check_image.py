from PIL import Image
import os

files = os.listdir("temp/temp2")
print("Files:", files[:3])
if files:
    img_path = os.path.join("temp/temp2", files[1])
    print("Checking:", img_path)
    try:
        img = Image.open(img_path)
        print("Size:", img.size)
        print("Format:", img.format)
    except Exception as e:
        print("Error:", e)