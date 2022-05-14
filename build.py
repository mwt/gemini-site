#!/bin/env python3

import os
from glob import glob
from subprocess import run
import yaml
from md2gemini import md2gemini

dist_folder = ".//dist"
DIRs = ("posts", "papers")

# clean untracked files
run(["git", "clean", "-dfx"], check=True)

# get a dictionary of markdown files
md_files = {DIR: glob(".//jekyll-files//_{DIR}//*.md".format(DIR=DIR)) for DIR in DIRs}

# make the dist folder
os.makedirs(dist_folder, exist_ok=True)
for DIR in DIRs:
    os.makedirs(os.path.join(dist_folder, DIR), exist_ok=True)


def split_frontmater(md_file):
    with open(md_file, "r", encoding="utf8") as f:
        mixed_text = f.read()

    if len(mixed_text) == 0:
        return ""

    # Pre processing
    # Remove frontmatter
    frontmatterExists = False
    lines = mixed_text.strip().splitlines()
    if lines[0] == "---":
        yaml_lines = []
        md_lines = []
        for i, line in enumerate(lines[1:]):  # Skip first front matter line
            if line == "---":
                # End of frontmatter, add all the lines below it
                yaml_lines.extend(lines[1:i])
                md_lines.extend(lines[i + 2 :])
                break
        # Turn it back into text
        if md_lines != []:
            frontmater = yaml.safe_load("\n".join(yaml_lines))
            markdown = "\n".join(md_lines)
            return frontmater, markdown
        # if markdown is empty, we don't want this file
        else:
            return False
    # if there is no frontmater
    else:
        return {}, mixed_text


for DIR in DIRs:
    for md_file in md_files[DIR]:
        file_split = split_frontmater(md_file)
        if file_split is not False:
            # get data from yaml and markdown
            data, markdown = file_split

            if "title" in data.keys():
                pre_md = "# " + data["title"] + "\n\n"
            else:
                pre_md = ""

            # convert to gemini
            gemini = md2gemini(pre_md + markdown)

            if "permalink" in data.keys():
                save_path = data["permalink"] + ".gmi"
            else:
                save_path = os.path.splitext(os.path.basename(md_file))[0] + ".gmi"
            with open(os.path.join(dist_folder, DIR, save_path), "w") as f:
                f.write(gemini)
