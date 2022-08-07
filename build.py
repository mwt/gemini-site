#!/bin/env python3

"""
Author: Matthew W. Thomas
Script to convert my WWW Jekyll site <https://www.matthewthom.as> to Gemini
"""

import shutil
import os
from glob import glob
from subprocess import run
import yaml
from md2gemini import md2gemini

JEKYLL_FOLDER = os.path.join(".", "jekyll-files")
DIST_FOLDER = os.path.join(".", "dist")
GEMINI_TEMPLATES = os.path.join(".", "gemini-templates")
DIRs = ("posts", "papers")

# clean untracked files
# run(["git", "clean", "-dfx"], check=True)

# get a dictionary of markdown files
md_files = {DIR: glob(os.path.join(JEKYLL_FOLDER, f"_{DIR}", "*.md")) for DIR in DIRs}

# make the dist folder
os.makedirs(DIST_FOLDER, exist_ok=True)
for DIR in DIRs:
    os.makedirs(os.path.join(DIST_FOLDER, DIR), exist_ok=True)


def split_frontmatter(md_file):
    """
    Take Jekyll md file and output tuple with yml dict and md string
    """
    with open(md_file, "r", encoding="utf8") as f:
        mixed_text = f.read()

    if len(mixed_text) == 0:
        return ""

    # Pre processing
    # Remove frontmatter
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
            frontmatter = yaml.safe_load("\n".join(yaml_lines))
            markdown = "\n".join(md_lines)
            return frontmatter, markdown
        # if markdown is empty, we don't want this file
        else:
            return False
    # if there is no frontmatter
    else:
        return {}, mixed_text


def process_library(DIR, make_files: bool = True):
    """
    Function to convert all markdown files in DIR directly to gmi
    """
    # prepare a string for the index file
    library_list = []
    for md_file in sorted(md_files[DIR], reverse=True):
        file_split = split_frontmatter(md_file)
        if file_split is not False:
            # get data from yaml and markdown
            data, markdown = file_split

            # convert to gemini
            gemini = md2gemini(markdown)
            data["content"] = gemini

            if make_files:
                data["has_gmi"] = True
                if "title" in data.keys():
                    gemini = "# " + data["title"] + "\n\n" + gemini
                if "permalink" in data.keys():
                    save_path = data["permalink"] + ".gmi"
                else:
                    save_path = os.path.splitext(os.path.basename(md_file))[0] + ".gmi"
                with open(
                    os.path.join(DIST_FOLDER, DIR, save_path), "w", encoding="utf8"
                ) as f:
                    f.write(gemini)
                data["gmi_path"] = os.path.join(DIR, save_path)
            library_list += [data]
    return library_list


# POSTS SECTION
# =============================================================================
# generate a gmi file for each post
gemini_posts = process_library("posts")
with open(os.path.join(GEMINI_TEMPLATES, "posts.gmi"), "r", encoding="utf8") as f:
    index_posts = (
        f.read()
        + "\n"
        + "\n".join(
            [
                f"=> {gemini_post['gmi_path']} {gemini_post['title']}"
                if "title" in gemini_post.keys()
                else f"=> {gemini_post['gmi_path']}"
                for gemini_post in gemini_posts
            ]
        )
        + "\n"
    )
with open(os.path.join(DIST_FOLDER, "posts", "index.gmi"), "w", encoding="utf8") as f:
    f.write(index_posts)


# PAPERS SECTION
# =============================================================================
# generate a gmi file for each post
gemini_papers = process_library("papers", make_files=False)
with open(os.path.join(GEMINI_TEMPLATES, "papers.gmi"), "r", encoding="utf8") as f:
    index_papers = f.read()

# construct index file from data and copy PDFs
for gemini_paper in gemini_papers:
    if "title" in gemini_paper.keys():
        index_papers += f"\n## {gemini_paper['title']}\n\n"
        if "content" in gemini_paper.keys():
            index_papers += gemini_paper["content"] + "\n\n"
        if "pdf" in gemini_paper.keys():
            pdf_path = os.path.join(JEKYLL_FOLDER, *gemini_paper["pdf"].split("/"))
            pdf_filename = os.path.basename(pdf_path)
            index_papers += f"=> {pdf_filename} Paper\n"
            shutil.copyfile(
                pdf_path,
                os.path.join(DIST_FOLDER, "papers", pdf_filename),
            )
        if "slides" in gemini_paper.keys():
            pdf_path = os.path.join(JEKYLL_FOLDER, *gemini_paper["slides"].split("/"))
            pdf_filename = os.path.basename(pdf_path)
            index_papers += f"=> {pdf_filename} Slides\n"
            shutil.copyfile(
                pdf_path,
                os.path.join(DIST_FOLDER, "papers", pdf_filename),
            )
with open(os.path.join(DIST_FOLDER, "papers", "index.gmi"), "w", encoding="utf8") as f:
    f.write(index_papers)
