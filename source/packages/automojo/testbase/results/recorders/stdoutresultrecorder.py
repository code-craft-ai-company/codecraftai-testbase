"""
    .. module:: automojo.testbase.results.recorders.stdoutresultrecorder
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: The default ``testbase`` result recorder for standalone runs — records the
               machine-readable JSOS/JSON artefacts and echoes the human-readable summary to
               stdout, without the integration-only HTML rendering.

    Plain ``testbase`` runs standalone (no ``automojo-runtime`` / ``automojo-this-app``) and has
    no HTML summary template or static-resource directory. :class:`StdoutResultRecorder` is the
    default recorder used by :class:`automojo.testbase.testjob.TestJob`: it reuses the JSOS stream
    and JSON summary serialisation (so the ``testbase agents`` machine CLI can still consume the
    artefacts), skips the HTML template / static-resource publication, and prints the run summary
    to stdout so results are visible without any reporting infrastructure.

    The integration runtime (``automojo-integration-runtime`` / ``IntegratedTestJob``) overrides
    ``TestJob._create_recorder`` to use the full HTML-rendering recorder instead.

    .. note::
        Phase-2 transitional design: this subclasses :class:`JsonResultRecorder` (which is
        import-clean of runtime/this-app) to reuse its JSON/JSOS serialisation. When the HTML
        rendering is split out of ``JsonResultRecorder`` into the integration runtime (Phase 3),
        this recorder is re-based onto the JSON/JSOS serialisation core that remains in
        ``testbase``. See ``REFACTOR-TESTBASE-INTEGRATION-RUNTIME-ROADMAP.md`` (§3, §7.2).

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from automojo.testbase.results.recorders.jsonresultrecorder import JsonResultRecorder


class StdoutResultRecorder(JsonResultRecorder):
    """
        Standalone result recorder that produces the JSOS/JSON artefacts and echoes the run
        summary to stdout, without the integration-only HTML rendering.
    """

    def initialize_report(self):
        """
            Standalone runs have no HTML summary template or static-resource directory to
            publish, so report initialisation is a no-op. The JSOS result stream and the JSON
            summary are still written by the inherited recorder behaviour.

            :returns: None
        """
        return

    def finalize(self):
        """
            Finalises the recording (reusing the inherited counters / result-determination and
            artefact writing) and then echoes the human-readable run summary to stdout exactly
            once, even though ``finalize`` may be invoked both explicitly and by the context
            manager's ``__exit__``.

            :returns: None
        """
        was_finalized = self._finalized

        super().finalize()

        if not was_finalized:
            summary_lines = self.format_lines()
            for line in summary_lines:
                print(line, flush=True)

        return
