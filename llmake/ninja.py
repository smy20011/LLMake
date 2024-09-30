from io import StringIO

from llmake.context import Context, LinkType
from llmake.markdown import Project, Task

from .ninja_syntax import Writer


def create_ninja_file(projfile: str, proj: Project):
    buildfile = StringIO()
    writer = Writer(buildfile)

    writer.rule(
        name="fetch",
        command="llmake fetch-context web-link $url $out",
        description="Fetch web page $url",
    )

    writer.rule(
        name="create_prompt",
        command="llmake create-prompt $in $task",
        description="Create prompt file for $task",
    )

    writer.rule(
        name="query",
        command="llmake query $in $out",
        description="Query LLM engine for $taskname",
    )

    all_contexts = proj.context + [ctx for task in proj.tasks for ctx in task.context]
    for ctx in all_contexts:
        if ctx.context_type == LinkType.WEB_LINK:
            writer.build(outputs=ctx.filename(), rule="fetch", variables={"url": ctx.target})

    for task in proj.tasks:
        contexts = proj.context + task.context
        context_deps = [ctx.filename() for ctx in contexts]
        task_deps = [t.result_filename() for t in proj.get_dependent_tasks(task)]
        writer.build(
            outputs=task.filename(),
            rule="create_prompt",
            inputs=projfile,
            implicit=context_deps + task_deps,
            variables={"task": task.slug()},
        )
        writer.build(
            outputs=task.result_filename(),
            rule="query",
            inputs=task.filename(),
            variables={"taskname": task.name},
        )

    return buildfile.getvalue()
