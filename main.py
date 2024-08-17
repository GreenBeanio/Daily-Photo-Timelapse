# Imports
import os
import pathlib
from PIL import Image, ExifTags, ImageOps, ImageDraw, ImageFont
import time
import datetime
import json
import cv2
import shutil

# User Settings
add_day_count = True
add_date = True
add_text_boxes = True
fps = 30
length_per_image = 2
rotate_image = 0
use_cheat_day = True
specific_first_date = datetime.date(2024, 1, 1)
delete_temp = True
delete_source = False

# Get the path for the photos
root = pathlib.Path().resolve()
photo_directory = pathlib.Path.joinpath(root, "photos")
output_directory = pathlib.Path.joinpath(root, "timelapse")
temp_directory = pathlib.Path.joinpath(root, "temp")
json_fix = pathlib.Path.joinpath(root, "corrections.json")

# Create future directories
if not pathlib.Path.exists(output_directory):
    pathlib.Path.mkdir(output_directory)
if not pathlib.Path.exists(temp_directory):
    pathlib.Path.mkdir(temp_directory)


# Creating a class to store image information
class ImageFiles:
    # Set it up
    def __init__(
        self, path: pathlib, creation: datetime, width: int, height: int
    ) -> None:
        self.path = path
        self.creation = creation
        self.width = width
        self.height = height

    # Get a readable string
    def __str__(self) -> str:
        return f"Creation: {self.creation}\nWidth: {self.width}\nHeight: {self.height}"

    # Special method for lt so we can sort by date time
    def __lt__(self, other):
        return self.creation < other.creation


date_corrections = {}
# Loading json for photos that need fixed
if pathlib.Path.exists(json_fix):
    with open(json_fix, "r") as file:
        temp_load = json.load(file)
    # Change the sting to datetimes
    for x, y in temp_load.items():
        date_corrections[x] = datetime.datetime.strptime(y, "%Y-%m-%d %H:%M:%S")


# Create a list of files
images = []

# Getting every photo in the photos path
for image_x in photo_directory.iterdir():
    # Check if it's a file
    if not image_x.is_file():
        print("uh oh")
        continue
    # Check if it's the correct type of image
    if not image_x.suffix in (".jpg", ".png"):
        print("wrong file")
        continue
    # Get file information (exif data) from Pillow
    image_x_i = Image.open(image_x).getexif()
    # Where to store readable keys
    temp_keys = {}
    # Check if the image has exif data
    if len(image_x_i) != 0:
        # Transform the exif tags into readable keys
        for key, val in image_x_i.items():
            if key in ExifTags.TAGS:
                # Check if the key is one we want
                if ExifTags.TAGS[key] in ("DateTime", "ImageLength", "ImageWidth"):
                    # Modifying the val if it's not an int (only will be datetime)
                    if not isinstance(val, int):
                        # Convert off of the exif date time format
                        val = datetime.datetime.strptime(val, "%Y:%m:%d %H:%M:%S")
                    # Add the keys
                    temp_keys[ExifTags.TAGS[key]] = val
    # We have to get this information from the file itself
    else:
        # Get the last time the file was modified (closest we'll get to exif data because
        # the "creation time" [ctime] can be change by many actions while the "modified time"
        # [mtime] only changes if the content of the file itself is modified. "access time" [atime]
        # is useless for this use case.)
        # Converting from the local date time representation since we just got it from there
        modified_time = datetime.datetime.strptime(
            time.ctime(os.path.getmtime(image_x)), "%c"
        )
        temp_keys["DateTime"] = modified_time
        t_w, t_h = Image.open(image_x).size
        # Yes length is width and width is height ... exif tags must be weird
        temp_keys["ImageLength"] = t_w
        temp_keys["ImageWidth"] = t_h
    # Get the data we want (creation, width, length)
    wanted_data = ImageFiles(
        image_x,
        temp_keys["DateTime"],
        temp_keys["ImageLength"],
        temp_keys["ImageWidth"],
    )
    # Add the image to the list
    images.append(wanted_data)


# Getting a list of the file paths that need updated
need_updated_paths = []
for x in date_corrections:
    need_updated_paths.append(pathlib.Path.joinpath(root, "photos", x))

# Checking images that need to have their dates fixed
for n, x in enumerate(images):
    if x.path in need_updated_paths:
        images[n].creation = date_corrections[images[n].path.name]

# Here's a step to fix any issues in the dates. In my example pictures for some reason
# a handful of pictures lost their modified time. So this step will be used to fix the
# date time of those pictures.
# From the images search for duplicate datetimes
date_time_count = {}
for x in images:
    if date_time_count.get(x.creation) is None:
        date_time_count[x.creation] = 1
    else:
        date_time_count[x.creation] += 1
# Sorting the dictionary. Kind of fucky honestly
sorted_count = sorted(date_time_count.items(), key=lambda x: x[1], reverse=True)
# Only getting returning dates with more than 1 date (because if the modification has been messed up it was probably to todays date)
output_sorted_count = []
for x in sorted_count:
    if x[1] > 1:
        output_sorted_count.append(x[0])
# Get the filenames to update
pictures_to_update = []
for x in images:
    if x.creation in output_sorted_count:
        pictures_to_update.append(x.path.name)
# Get the user to update the datetimes of these (preferably they'd have their phone or wherever they took them to get the correct datetime)
for x in pictures_to_update:
    while True:
        user_answer = input(
            f'What is the correct time the picture "{x}" was taken at?\nAnswer in the following format: YYYY:MM:DD HH:MM:SS\n'
        )
        try:
            new_time = datetime.datetime.strptime(user_answer, "%Y/%m/%d %H:%M:%S")
            date_corrections[x] = new_time
            break
        except:
            print("That time was invalid.")
# Save these updates for later!
with open(json_fix, "w+") as file:
    json_obj = json.dumps(date_corrections, indent=4, sort_keys=False, default=str)
    file.write(json_obj)

# Sorting the images by their date (defined in the class __lt__ method)
images.sort()

size_count = {}
# Get the most common image size
for x in images:
    str_match = str(x.width) + " " + str(x.height)
    if size_count.get(str_match) is None:
        size_count[str_match] = {"Width": x.width, "Height": x.height, "Count": 1}
    else:
        size_count[str_match]["Count"] += 1
common_size = ""
temp_size = 0
for x, y in size_count.items():
    if y["Count"] > temp_size:
        common_size = x
        temp_size = y["Count"]
scale_size = (size_count[common_size]["Width"], size_count[common_size]["Height"])
font = ImageFont.load_default(size=200)
# Get the first date
if specific_first_date is None:
    first_date = images[0].creation.date()
else:
    first_date = specific_first_date
# Resizing the images
for n, x in enumerate(images):
    with Image.open(x.path) as im:
        name = pathlib.Path.joinpath(temp_directory, x.path.name)
        # Sets the image to follow the transposing in the exif tag
        im = ImageOps.exif_transpose(im)
        # Rotate if we are rotating
        if rotate_image != 0:
            im = im.rotate(rotate_image)
        # Resize the image
        if im.size != scale_size:
            im = ImageOps.cover(im, scale_size)
        draw = ImageDraw.Draw(im, "RGBA")
        # Add day counter
        if add_day_count:
            day_string = f"Day: {n+1}"
            day_string_length = len(day_string) - 5
            polygon_width = 525 + (day_string_length * 115)
            if add_text_boxes:
                draw.polygon(
                    [
                        (35, 25),
                        (35, 245),
                        (polygon_width, 245),
                        (polygon_width, 25),
                    ],
                    fill=(255, 255, 255, 75),
                )
            draw.text(
                (50, -5),
                day_string,
                font=font,
                fill=(0, 0, 0, 100),
                anchor="la",
            )
        if add_date:
            if add_text_boxes:
                draw.polygon(
                    [
                        (im.size[0] - 35, im.size[1] - 25),
                        (im.size[0] - 35, im.size[1] - 245),
                        (im.size[0] - 1100, im.size[1] - 245),
                        (im.size[0] - 1100, im.size[1] - 25),
                    ],
                    fill=(255, 255, 255, 75),
                )
            date_to_use = str(x.creation.date())
            if use_cheat_day:
                date_to_use = first_date + datetime.timedelta(days=n)
            draw.text(
                (im.size[0] - 50, im.size[1] - 72),
                f"{date_to_use}",
                font=font,
                fill=(0, 0, 0, 100),
                anchor="rs",
            )
        # Save the image
        im.save(name)

output_video = cv2.VideoWriter(
    pathlib.Path.joinpath(output_directory, "timelapse.mp4"),
    fourcc=cv2.VideoWriter_fourcc(*"mp4v"),
    fps=fps,
    frameSize=scale_size,
)

# Creating a video using opencv
for n, x in enumerate(images):
    # Get name of the image for a frame
    name = pathlib.Path.joinpath(temp_directory, x.path.name)
    # Read the image with openCV
    img = cv2.imread(name)
    # For however many frames we want per image add it to the video
    for i in range(length_per_image):
        output_video.write(img)
# Don't think I have any windows, but might as well make sure
cv2.destroyAllWindows()
output_video.release()

# Delete files
if delete_temp:
    shutil.rmtree(temp_directory)
if delete_source:
    shutil.rmtree(photo_directory)
