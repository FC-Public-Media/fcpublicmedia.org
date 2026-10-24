"""site/ is static files: no host config and no server code may live in it. The running code is FC-Public-Media/site-worker."""
import pathlib
import subprocess
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]

# Each makes a host run something, or binds the site to one host.
FORBIDDEN = ("wrangler.json", "wrangler.jsonc", "wrangler.toml", "staticwebapp.config.json", "_worker.js",
             "netlify.toml", "vercel.json")
FORBIDDEN_DIRS = ("functions", "api", "netlify")


def tracked():
    out = subprocess.run(["git", "ls-files", "site"], cwd=REPO, capture_output=True, text=True, check=True)
    return [pathlib.PurePosixPath(p) for p in out.stdout.split()]


def offenders(paths):
    return [str(p) for p in paths
            if p.name in FORBIDDEN or (len(p.parts) > 2 and p.parts[1] in FORBIDDEN_DIRS)]


class SiteRunsNoCode(unittest.TestCase):
    def test_site_holds_no_host_config_or_server_code(self):
        self.assertEqual(offenders(tracked()), [], "site/ is static; running code belongs in FC-Public-Media/site-worker")

    def test_the_check_would_notice(self):
        for sample in ("site/wrangler.jsonc", "site/staticwebapp.config.json", "site/functions/checkout.js",
                       "site/_worker.js"):
            self.assertEqual(offenders([pathlib.PurePosixPath(sample)]), [sample])
        self.assertEqual(offenders([pathlib.PurePosixPath("site/assets/js/broker.js")]), [])


if __name__ == "__main__":
    unittest.main()
