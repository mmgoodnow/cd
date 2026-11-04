import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).parent
WORKFLOWS = ("docker.yml", "docker-amd64.yml")
CURRENT = "a" * 40
OLD = "b" * 40


def guards(contents):
    marker = "      - name: Check current source revision\n"
    return [textwrap.dedent(section.split("        run: |\n", 1)[1].split("\n      - name:", 1)[0])
            for section in contents.split(marker)[1:]]


class PublicationOrderTest(unittest.TestCase):
    def run_guard(self, source, *, head=CURRENT, build=CURRENT, ref="refs/heads/main", fail=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            gh = root / "gh"
            gh.write_text('#!/bin/bash\nset -eu\nprintf "%s\\n" "$@" > "$GH_CALLS"\n'
                          'if [ "$FAKE_GH_FAIL" = 1 ]; then exit 42; fi\n'
                          'printf "%s\\n" "$FAKE_HEAD"\n')
            gh.chmod(0o700)
            output = root / "output"
            result = subprocess.run(["bash", "-c", source], capture_output=True, text=True, env={
                **os.environ, "PATH": str(root) + os.pathsep + os.environ["PATH"],
                "GITHUB_REPOSITORY": "Owner/Example", "GITHUB_REF": ref, "GITHUB_SHA": build,
                "GITHUB_OUTPUT": str(output), "GH_CALLS": str(root / "calls"),
                "FAKE_HEAD": head, "FAKE_GH_FAIL": "1" if fail else "0",
            })
            calls = (root / "calls").read_text().splitlines()
            self.assertEqual(calls, ["api", f"repos/Owner/Example/commits/{ref}", "--jq", ".sha"])
            return result, output.read_text() if output.exists() else ""

    def test_both_workflows_serialize_only_publication_and_deployment(self):
        for name in WORKFLOWS:
            contents = (ROOT / ".github/workflows" / name).read_text()
            build, publication = contents.split("\n  manifest:\n", 1)
            self.assertNotIn("concurrency:", build)
            for job in publication.split("\n  watchtower-update:\n"):
                self.assertIn("group: cd-publish-${{ github.repository }}-${{ github.ref }}", job)
                self.assertIn("queue: max", job)
                self.assertIn("cancel-in-progress: false", job)
            self.assertIn("published: ${{ steps.current.outputs.publish }}", publication)
            self.assertIn("if: needs.manifest.outputs.published == 'true'", publication)
            self.assertEqual(publication.count("if: steps.current.outputs.publish == 'true'"), 3)
            self.assertIn("if: always() && steps.current.outputs.publish == 'true'", publication)

    def test_every_side_effect_guard_uses_the_same_checked_source(self):
        sources = [source for name in WORKFLOWS
                   for source in guards((ROOT / ".github/workflows" / name).read_text())]
        self.assertEqual(len(sources), 4)
        self.assertEqual(len(set(sources)), 1)
        self.source = sources[0]

    def test_current_revision_can_publish_and_deploy_for_branches_and_tags(self):
        source = guards((ROOT / ".github/workflows/docker.yml").read_text())[0]
        for ref in ("refs/heads/main", "refs/heads/fix/image-tags", "refs/tags/v1.2.3"):
            result, output = self.run_guard(source, ref=ref)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output, "publish=true\n")

    def test_late_old_build_or_rerun_cannot_roll_back_a_newer_publication(self):
        source = guards((ROOT / ".github/workflows/docker.yml").read_text())[0]
        for ordering in ((OLD, CURRENT), (CURRENT, OLD)):
            published = []
            for build in ordering:
                result, output = self.run_guard(source, build=build)
                self.assertEqual(result.returncode, 0, result.stderr)
                if output == "publish=true\n":
                    published.append(build)
            self.assertEqual(published, [CURRENT])

    def test_ref_advancing_between_publication_and_watchtower_skips_deployment(self):
        source = guards((ROOT / ".github/workflows/docker.yml").read_text())[0]
        self.assertEqual(self.run_guard(source)[1], "publish=true\n")
        self.assertEqual(self.run_guard(source, head=OLD)[1], "publish=false\n")

    def test_lookup_failure_cannot_authorize_a_side_effect(self):
        source = guards((ROOT / ".github/workflows/docker.yml").read_text())[0]
        result, output = self.run_guard(source, fail=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output, "")


if __name__ == "__main__":
    unittest.main()
