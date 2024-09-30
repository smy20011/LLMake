from io import StringIO

from llmake.context import Context, LinkType
from llmake.markdown import Project, Task


def create_makefile(projfile: str, proj: Project):
    buildfile = StringIO()

    all_tasks = [task.result_filename() for task in proj.tasks]
    all_files = []
    print("all:", " ".join(all_tasks), file=buildfile)

    all_contexts = proj.context + [ctx for task in proj.tasks for ctx in task.context]
    for ctx in all_contexts:
        if ctx.context_type == LinkType.WEB_LINK:
            buildfile.write(make_context(ctx.target, ctx.filename()))
            all_files.append(ctx.filename())

    for task in proj.tasks:
        contexts = proj.context + task.context
        context_deps = [ctx.filename() for ctx in contexts]
        task_deps = [t.result_filename() for t in proj.get_dependent_tasks(task)]
        buildfile.write(make_task(projfile, task, context_deps + task_deps))
        all_files.append(task.filename())
        all_files.append(task.result_filename())

    print(
        f"""
clean:
\t@echo "Cleaning up generated files..."
\t@rm "{'" "'.join(all_files)}"
""",
        file=buildfile,
    )

    return buildfile.getvalue()


def make_context(url, output):
    return f"""
{output}:
\t@echo "Fetching webpage from {url}..."
\t@llmake fetch-context web-link {url} {output}
"""


def make_task(projfile, task: Task, deps):
    return f"""
{task.filename()}: {projfile} {" ".join(deps)}
\t@echo "Generating prompt file: {task.filename()}..."
\t@llmake create-prompt {projfile} {task.slug()}

{task.result_filename()}: {task.filename()}
\t@echo "Querying LLM to generate result for task: {task.name}..."
\t@llmake query {task.filename()} {task.result_filename()}
"""
