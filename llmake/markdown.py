import re
from dataclasses import dataclass
from re import Pattern

from mistletoe import Document
from mistletoe.block_token import Heading
from mistletoe.span_token import Link, RawText, SpanToken, add_token, remove_token
from mistletoe.token import Token

from llmake.naming import slugify

from .context import Context, LinkType


@dataclass
class Task:
    name: str
    prompt: list[str]
    context: list[Context]
    dependency: list[str]

    def slug(self):
        return slugify(self.name)


@dataclass
class Project:
    prompt: list[str]
    tasks: list[Task]
    context: list[Context]


def _match_header(level: int, matcher: Pattern):
    def fn(token: Token) -> bool:
        if not isinstance(token, Heading):
            return False
        if token.level != level:
            return False
        children = list(token.children or [])
        if len(children) == 0:
            return False
        title = children[0]
        if not isinstance(title, RawText):
            return False
        return matcher.match(title.content)

    return fn


MATCH_TASK_HEADER = _match_header(1, re.compile("tasks", re.IGNORECASE))
MATCH_LEVEL1_HEADER = _match_header(1, re.compile(".*"))
MATCH_LEVEL2_HEADER = _match_header(2, re.compile(".*"))


def parse_markdown(markdown: str):
    lines = markdown.splitlines()
    doc = Document(lines)
    children = list(doc.children or [])
    # Task represents all task boundaries, ith task have line range [tasks[i], tasks[i+1])
    task_lines = []
    in_task = False
    for child in children:
        if not in_task and MATCH_TASK_HEADER(child):
            in_task = True
            continue
        if in_task and MATCH_LEVEL2_HEADER(child):
            task_lines.append(getattr(child, "line_number", -1) - 1)
        if in_task and MATCH_LEVEL1_HEADER(child):
            in_task = False
            task_lines.append(getattr(child, "line_number", -1) - 1)
    if in_task:
        task_lines.append(len(lines))

    tasks = []
    for start, end in zip(task_lines, task_lines[1:]):
        links = get_context_links(lines[start:end])
        dependency = [link.target for link in links if link.context_type == LinkType.HEAD_LINK]
        context = [link for link in links if link.context_type != LinkType.HEAD_LINK]
        if not dependency:
            dependency = [t.name for t in tasks]
        name = lines[start][2:].lstrip()
        tasks.append(Task(name, lines[start:end], context, dependency))

    prompt_wihtout_task = lines[: task_lines[0]] + lines[task_lines[-1] :]
    context = get_context_links(prompt_wihtout_task)

    return Project(prompt_wihtout_task, tasks, context)


class WikiLinkToken(SpanToken):
    pattern = re.compile(r"\[\[ *(.+?) *\]\]")

    def __init__(self, match):
        target = match.group(1)
        if "|" in target:
            target, self.name = target.split()
        else:
            self.name = target
        if target.startswith("#"):
            self.target = target[1:]
            self.link_type = LinkType.HEAD_LINK
        else:
            self.target = target
            self.link_type = LinkType.WIKI_LINK


def get_context_links(prompt: str | list[str]) -> list[Context]:
    add_token(WikiLinkToken)
    doc = Document(prompt)
    remove_token(WikiLinkToken)

    context = []

    def dfs(token: Token):
        if isinstance(token, WikiLinkToken):
            context.append(Context(token.link_type, token.name, token.target))
        if isinstance(token, Link):
            children = list(token.children or [])
            name = children[0].content if children and isinstance(children[0], RawText) else ""
            context.append(Context(LinkType.WEB_LINK, name, token.target))
        if token.children:
            for child in token.children:
                dfs(child)

    dfs(doc)
    return context
