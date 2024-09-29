import json
import sys
from collections.abc import Iterable
from dataclasses import asdict
from pathlib import Path

from cyclopts import App
from mistletoe.ast_renderer import AstRenderer
from mistletoe.html_renderer import HTMLRenderer

import llmake.context as ctx
from llmake.context import Context, LinkType
from llmake.markdown import parse_markdown
from llmake.naming import slugify

app = App()


@app.default
def default(file):
    with Path.open(file) as f:
        print(json.dumps(asdict(parse_markdown(f.read())), indent=2))


@app.command
def fetch_context(context_type: LinkType, uri: str, output_file: str):
    context = Context(context_type, "", uri)
    result = ctx.fetch_context(context, str(Path.cwd()))
    if result:
        maybe_write(output_file, result)
    else:
        print(f"Failed to fetch context {context}")
        sys.exit(-1)


@app.command
def create_prompt(input_file: str, task_name: str):
    with Path(input_file).open() as f:
        doc = parse_markdown(f.read())
        task = None
        for t in doc.tasks:
            if slugify(t.name) == task_name:
                task = t
        if not task:
            print(f"Cannot find task {task_name}")
            sys.exit(-1)
        result = doc.prompt.copy()
        result.append("# Contexts")
        contexts = doc.context + task.context
        for ctx, content in zip(contexts, load_fetched_context(contexts)):
            result.append(f"## {ctx.name}")
            result.append(content)
        result.append("# Task")
        result.extend(task.prompt)

    maybe_write(task_name + ".prompt.md", "\n".join(result))


def maybe_write(filename: str, content: str):
    """Update the content of file only if the content is different."""
    p = Path(filename)
    if p.exists():
        old = p.open().read()
        if old == content:
            return
    with p.open("w") as f:
        f.write(content)


def load_fetched_context(contexts: list[Context]) -> Iterable[str]:
    for context in contexts:
        match context.context_type:
            case LinkType.WIKI_LINK:
                yield ctx.fetch_context(context) or ""
            case LinkType.WEB_LINK:
                fetched_filename = slugify(context.name)
                with Path(fetched_filename).open() as f:
                    yield f.read()
            case _:
                yield ""


def run_app():
    app()
