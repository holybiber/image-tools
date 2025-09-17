# Python tools for image collections

## distill_images

Select every nth image from input folders and copy them to an output folder. Intended to get a manageable selection suitable to watch as a family in a reasonable time. Example:

```
cd ~/bilder/wir/
python3 ~/coding/python/image-tools/distill_images.py --input-folders 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025 -n 20 -o 5 --output-folder ~/bildertodo/diverse/2016-2025\ jedes\ 20te\ Offset\ 5/
```
