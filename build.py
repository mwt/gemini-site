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
from gemfeed import build_feed

WWW_URL = "https://matthewthom.as"
JEKYLL_FOLDER = os.path.join(".", "jekyll-files")
DIST_FOLDER = os.path.join(".", "dist")
GEMINI_TEMPLATES = os.path.join(".", "gemini-templates")
DATA_FOLDER = os.path.join(JEKYLL_FOLDER, "_data")

DIRs = ("about", "projects", "posts", "papers")

# clean untracked files
run(["git", "clean", "-dfx"], check=True)

# get a dictionary of markdown files
md_files = {DIR: glob(os.path.join(JEKYLL_FOLDER, f"_{DIR}", "*.md")) for DIR in DIRs}

# make the dist folder
os.makedirs(DIST_FOLDER, exist_ok=True)
for DIR in DIRs:
    os.makedirs(os.path.join(DIST_FOLDER, DIR), exist_ok=True)

# symlink assets from www
os.symlink(
    r"../site/assets", os.path.join(DIST_FOLDER, "assets"), target_is_directory=True
)


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


def convert_links(url: str):
    """
    Function to convert links found in markdown
    Run by md2gemini in process_library function
    """
    if url.startswith("/"):
        if url.startswith("/papers/") and url.endswith("/"):
            return url[:-1] + ".pdf"
        elif url.startswith("/posts/"):
            # temporary fix
            return "/posts/"
        elif url.startswith("/assets/"):
            # this folder is symlinked
            return url
        else:
            return WWW_URL + url
    else:
        return url


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
            gemini = md2gemini(
                markdown, links="paragraph", strip_html=True, link_func=convert_links
            )
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


def project_list(yaml_list: str):
    """
    Construct my project lists (eg. on index page)
    """
    list_output = ""
    for p in yaml.safe_load(yaml_list):
        list_output += f"### {p['title']}\n{p['description']}\n"
        if "url" in p.keys():
            # check if link is relative
            if p["url"].startswith("/"):
                list_output += f"=> {WWW_URL}{p['url']} Link\n"
            else:
                list_output += f"=> {p['url']} Link\n"
        if "github" in p.keys():
            # check if link is relative
            if p["github"].startswith("/"):
                list_output += f"=> {WWW_URL}{p['github']} GitHub\n"
            else:
                list_output += f"=> {p['github']} GitHub\n"
        list_output += "\n"
    return list_output


# ROOT INDEX SECTION
# =============================================================================
# generate the primary index file for the site
shutil.copyfile(
    os.path.join(GEMINI_TEMPLATES, "index.gmi"), os.path.join(DIST_FOLDER, "index.gmi")
)


# ABOUT SECTION
# =============================================================================
# generate the primary index file for the site
shutil.copyfile(
    os.path.join(GEMINI_TEMPLATES, "about.gmi"),
    os.path.join(DIST_FOLDER, "about", "index.gmi"),
)


# PROJECTS SECTION
# =============================================================================
# generate the projects page from data files

# load template
with open(os.path.join(GEMINI_TEMPLATES, "projects.gmi"), "r", encoding="utf8") as f:
    index_root = f.read()

# Academic projects
index_root += "## Academic Projects\n\n"
with open(
    os.path.join(DATA_FOLDER, "projects-academic.yml"), "r", encoding="utf8"
) as f:
    index_root += project_list(f.read()) + "\n\n"

# Professional projects
index_root += "## Professional Projects\n\n"
with open(
    os.path.join(DATA_FOLDER, "projects-professional.yml"), "r", encoding="utf8"
) as f:
    index_root += project_list(f.read()) + "\n\n"

# Personal projects
index_root += "## Personal Projects\n\n"
with open(
    os.path.join(DATA_FOLDER, "projects-personal.yml"), "r", encoding="utf8"
) as f:
    index_root += project_list(f.read()) + "\n\n"

# Gist projects
index_root += "## Code Snippets\n\n"
with open(os.path.join(DATA_FOLDER, "projects-gists.yml"), "r", encoding="utf8") as f:
    index_root += project_list(f.read()) + "\n\n"

with open(
    os.path.join(DIST_FOLDER, "projects", "index.gmi"), "w", encoding="utf8"
) as f:
    f.write(index_root)


# POSTS SECTION
# =============================================================================
# generate a gmi file for each post and create an index
gemini_posts = process_library("posts")
with open(os.path.join(GEMINI_TEMPLATES, "posts.gmi"), "r", encoding="utf8") as f:
    index_posts = f.read() + "\n"

for gemini_post in gemini_posts:
    file_filename = os.path.basename(gemini_post["gmi_path"])
    index_posts += f"=> {file_filename}"
    if "title" in gemini_post.keys():
        index_posts += " " + gemini_post["title"]
    index_posts += "\n"

with open(os.path.join(DIST_FOLDER, "posts", "index.gmi"), "w", encoding="utf8") as f:
    f.write(index_posts)


# PAPERS SECTION
# =============================================================================
# generate a a page that lists my papers and links to PDFs
gemini_papers = process_library("papers", make_files=False)
with open(os.path.join(GEMINI_TEMPLATES, "papers.gmi"), "r", encoding="utf8") as f:
    index_papers = f.read()

# construct index file from data and copy PDFs
for gemini_paper in gemini_papers:
    if "title" in gemini_paper.keys():
        index_papers += f"\n## {gemini_paper['title']}\n"
        if "content" in gemini_paper.keys():
            index_papers += gemini_paper["content"] + "\n\n"
        if "pdf" in gemini_paper.keys():
            index_papers += f"=> {gemini_paper['pdf']} Paper\n"
        if "slides" in gemini_paper.keys():
            index_papers += f"=> {gemini_paper['slides']} Slides\n"
with open(os.path.join(DIST_FOLDER, "papers", "index.gmi"), "w", encoding="utf8") as f:
    f.write(index_papers)


build_feed(
    directory=os.path.join(DIST_FOLDER, "posts"),
    base_url="gemini://gemini.matthewthom.as/posts/",
    output=os.path.join("..", "atom.xml"),
    title="Matthew W. Thomas' Posts",
    subtitle="On Math, Economics, and Technology",
    author="Matthew W. Thomas'",
)
