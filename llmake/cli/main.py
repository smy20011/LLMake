import json
import sys
from dataclasses import asdict
from pathlib import Path

from cyclopts import App
from mistletoe.ast_renderer import AstRenderer
from mistletoe.html_renderer import HTMLRenderer

import llmake.context as ctx
from llmake.context import Context, LinkType
from llmake.markdown import parse_markdown

app = App()


@app.default
def default(file):
    with Path.open(file) as f:
        print(json.dumps(asdict(parse_markdown(f.read())), indent=2))


@app.command
def fetch_context(context_type: LinkType, uri: str, output_file: str):
    context = Context(context_type, "", uri)
    with Path(output_file).open("w") as f:
        result = ctx.fetch_context(context, str(Path.cwd()))
        if result:
            f.write(result)
        else:
            print(f"Failed to fetch context {context}")
            sys.exit(-1)


def run_app():
    app()
