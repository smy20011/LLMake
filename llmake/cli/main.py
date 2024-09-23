import json
from dataclasses import asdict
from pathlib import Path

from cyclopts import App
from mistletoe.ast_renderer import AstRenderer
from mistletoe.html_renderer import HTMLRenderer

from llmake.markdown import parse_markdown

app = App()


@app.default
def default(file):
    with Path.open(file) as f:
        print(json.dumps(asdict(parse_markdown(f.read())), indent=2))


def run_app():
    app()
