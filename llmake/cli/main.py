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
from llmake.markdown import Task, parse_markdown
from llmake.naming import slugify
from llmake.ninja import create_ninja_file

app = App()


@app.default
def create_ninja(file):
    with Path(file).open() as f:
        proj = parse_markdown(f.read())
        buildfile = create_ninja_file(file, proj)

    with Path("build.ninja").open("w") as f:
        f.write(buildfile)


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
        result.append("# Previous Finished Tasks")
        for dep_task in doc.get_dependent_tasks(task):
            result.append(f"## {dep_task.name}")
            result.append(load_task_result(dep_task))
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
                with Path(context.filename()).open() as f:
                    yield f.read()
            case LinkType.HEAD_LINK:
                yield ""


def load_task_result(task: Task) -> str:
    with Path(task.filename()).open() as f:
        return f.read()


def run_app():
    app()
