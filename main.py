from PIL import Image
from pathlib import Path
import numpy as np
from time import perf_counter
import argparse

parser = argparse.ArgumentParser(
    description="Finds and removes identical pictures in a folder.")
parser.add_argument("folder", type=Path,
                    help="The folder in which to remove identical pictures.")
parser.add_argument(
    "--dry-run",
    dest="dry_run",
    default=False,
    action=argparse.BooleanOptionalAction,
    help="Only prints which files are supposed to be removed.")

args = parser.parse_args()

load_start = perf_counter()

images = []  # Tuple of file path, numpy array scaled to 128x128, and dimension


lossy_suffixes = [".jpg", ".jpeg"]
lossless_suffixes = [".png"]
suffixes = lossy_suffixes + lossless_suffixes
for file_path in args.folder.iterdir():
    if file_path.is_file() and file_path.suffix in suffixes:
        im = Image.open(file_path)
        dim = im.size
        im = im.resize((128, 128)).convert("RGB")
        buff = np.asarray(im)
        images.append((file_path, buff, dim))

print("Loaded all images in %0.2f seconds" % (perf_counter() - load_start,))


def compare_images(buff1, buff2):
    sub = buff1 - buff2
    s = sub.sum() / 255
    return s < ((128*128) * 0.05)  # 5% margin of error


for i in range(len(images)):
    for j in range(i + 1, len(images)):
        try:
            i_path, i_buff, i_dim = images[i]
            j_path, j_buff, j_dim = images[j]
        except IndexError:
            continue  # Invalid index

        if compare_images(i_buff, j_buff):
            # Choose the better, higher resolution one
            i_pixels = i_dim[0] * i_dim[1]
            j_pixels = j_dim[0] * j_dim[1]
            if i_pixels > j_pixels:
                better = i
                worse = j
            elif j_pixels > i_pixels:
                better = j
                worse = i
            else:
                # Check by file format
                if j_path.suffix in lossless_suffixes \
                   and i_path.suffix in lossy_suffixes:
                    better = j
                    worse = i
                else:
                    # Arbitrary choice of the first one
                    better = i
                    worse = j

            print(images[better][0], images[worse][0])

            if not args.dry_run:
                images[worse][0].unlink()

            del images[worse]
