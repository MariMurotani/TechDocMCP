import re

import frontmatter
import markdown
from bs4 import BeautifulSoup


def extract_from_html(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n")


def extract_from_md(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        md = frontmatter.load(f)
        body = md.content
    html = markdown.markdown(body)
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n")


def extract_text(path):
    if path.endswith(".html"):
        return extract_from_html(path)
    if path.endswith(".md"):
        return extract_from_md(path)
    return ""
