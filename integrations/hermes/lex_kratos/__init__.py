"""lex_kratos — Hermes Agent plugin exposing the Lex Kratos judicial pipeline.

Drop this directory into ``~/.hermes/plugins/lex_kratos/`` and run ``hermes`` →
``/plugins`` to verify the tools ``lex_intake`` and ``lex_run_pipeline`` load.
See README.md.
"""

# Support both Hermes plugin-loading styles (package import or dir-on-path).
try:  # pragma: no cover - import-style shim
    from . import schemas, tools
except ImportError:  # pragma: no cover
    import schemas  # type: ignore[no-redef]
    import tools  # type: ignore[no-redef]


def register(ctx):
    """Wire the two tools into Hermes at startup."""
    ctx.register_tool(
        name="lex_intake",
        toolset="lex_kratos",
        schema=schemas.LEX_INTAKE,
        handler=tools.lex_intake,
    )
    ctx.register_tool(
        name="lex_run_pipeline",
        toolset="lex_kratos",
        schema=schemas.LEX_RUN_PIPELINE,
        handler=tools.lex_run_pipeline,
    )
