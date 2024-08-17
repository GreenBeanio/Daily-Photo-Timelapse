# Imports
import os
import sys
import pathlib
from PIL import Image, ExifTags
import time
import datetime
import typing
import json

# Get the path for the photos
root = pathlib.Path().resolve()
photo_directory = pathlib.Path.joinpath(root, "photos")
output_directory = pathlib.Path.joinpath(root, "timelapse")
json_fix = pathlib.Path.joinpath(root, "corrections.json")
print(json_fix)


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
update_dates = {}
for x in pictures_to_update:
    while True:
        user_answer = input(
            f'What is the correct time the picture "{x}" was taken at?\nAnswer in the following format: YYYY:MM:DD HH:MM:SS\n'
        )
        try:
            new_time = datetime.datetime.strptime(user_answer, "%Y/%m/%d %H:%M:%S")
            update_dates[x] = new_time
            break
        except:
            print("That time was invalid.")
# Save these updates for later!
with open(json_fix, "a+") as file:
    json.dumps(update_dates, indent=4, sort_keys=True, default=str)

# Sorting the images by their date (defined in the class __lt__ method)
images.sort()
