import os
import shutil
import argparse
from typing import List, Optional


# Function to gather every nth image from multiple folders
# and copy them to an output folder
def distill_images(
    input_folders: List[str],
    n: int,
    offset: Optional[int],
    output_folder: str
) -> None:
    os.makedirs(output_folder, exist_ok=True)

    if offset is None:
        offset = 0

    for folder in input_folders:
        if not os.path.isdir(folder):
            print(f"Skipping non-existent folder: {folder}")
            continue

        images = sorted([f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))])
        selected_images = images[offset::n]  # Take every nth image

        for image in selected_images:
            src_path = os.path.join(folder, image)
            dest_path = os.path.join(output_folder, image)
            shutil.copy2(src_path, dest_path)
            print(f"Copied: {src_path} -> {dest_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Select every nth image from given folders and copy them to an output folder.")
    parser.add_argument("--input-folders", nargs='+', required=True, help="List of input folders.")
    parser.add_argument("-n", type=int, required=True, help="Take every nth image.")
    parser.add_argument("-o", type=int, required=False, help="offset")
    parser.add_argument("--output-folder", required=True, help="Folder where selected images will be copied.")

    args = parser.parse_args()
    distill_images(args.input_folders, args.n, args.o, args.output_folder)
