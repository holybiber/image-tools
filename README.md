# Python tools for image collections

Developed using AI (gather_images.py with Claude.ai)

## distill_images.py

Select every nth image from input folders and copy them to an output folder. Intended to get a manageable selection suitable to watch as a family in a reasonable time. Example:

```
cd ~/bilder/wir/
python3 ~/coding/python/image-tools/distill_images.py --input-folders 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025 -n 20 -o 5 --output-folder ~/bildertodo/diverse/2016-2025\ jedes\ 20te\ Offset\ 5/
```

## gather_images.py

Gather images from a specified time span from several input folders (coming in from smartphones with FolderSync via Nextcloud), do some cleanup and put them in a structured way in the desired output folder.
See config.ini for the configuration.

Usage:

```
python3 gather_images.py --from-date 2025-05-01
```