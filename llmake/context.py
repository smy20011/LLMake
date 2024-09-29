import logging
import os
import os.path
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import newspaper

from llmake.naming import slugify


class LinkType(StrEnum):
    WEB_LINK = "web_link"
    WIKI_LINK = "wiki_link"
    HEAD_LINK = "head_link"


@dataclass
class Context:
    context_type: LinkType
    name: str
    target: str

    def slug(self):
        return slugify(self.name)


def fetch_context(context: Context, base_dir: str | None = None):
    match context.context_type:
        case LinkType.WEB_LINK:
            return fetch_external_link(context.target)
        case LinkType.WIKI_LINK:
            return fetch_local_file(context.target, base_dir)
    return None


def fetch_local_file(target: str, base_dir: str | None):
    if not base_dir:
        base_dir = str(Path.cwd())
    for root, _, files in os.walk(base_dir):
        for filename in files:
            if filename.startswith(target):
                return (Path(root) / filename).open().read()
    return None


def fetch_external_link(target: str):
    try:
        return newspaper.article(target).text
    except newspaper.ArticleException as e:
        logging.info("Failed to fetch context: ", target, e)
        return None
