import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest
from urllib.parse import parse_qsl, urlsplit


class WatchtowerScopeTest(unittest.TestCase):
    def test_both_workflows_replace_image_filters_with_only_calling_repo(self):
        for workflow in ("docker.yml", "docker-amd64.yml"):
            contents = (Path(__file__).parent / ".github/workflows" / workflow).read_text()
            self.assertIn("update_url=$(python3 - <<'PY'", contents)
            source = contents.split("update_url=$(python3 - <<'PY'\n", 1)[1].split("          PY\n", 1)[0]
            source = textwrap.dedent(source)
            for query in ("", "?image=unrelated/image", "?image=a&image=b&scope=keep"):
                with self.subTest(workflow=workflow, query=query):
                    result = subprocess.check_output(
                        [sys.executable, "-c", source],
                        env={**os.environ, "WATCHTOWER_UPDATE_URL": "https://example.invalid/v1/update" + query,
                             "GITHUB_REPOSITORY": "MmGoodnow/Podible"},
                        text=True,
                    ).strip()
                    parsed = urlsplit(result)
                    params = parse_qsl(parsed.query)
                    self.assertEqual([value for key, value in params if key == "image"], ["ghcr.io/mmgoodnow/podible"])
                    self.assertEqual(parsed.path, "/v1/update")
                    if "scope=keep" in query:
                        self.assertIn(("scope", "keep"), params)
            self.assertIn('"$update_url")', contents)


if __name__ == "__main__":
    unittest.main()
