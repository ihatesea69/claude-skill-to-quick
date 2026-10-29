import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "converter"))
import claude2quick as c  # noqa: E402

BODY = "# Title\n\nStep 1: read `references/a.md`.\nStep 2: keep $VAR and {braces}.\n"


def make_skill(root: Path, name="demo-skill", newline="\n", body=BODY, with_ref=True):
    d = root / name
    (d / "references").mkdir(parents=True)
    if with_ref:
        (d / "references" / "a.md").write_text("ref", encoding="utf-8")
    text = f"---\nname: {name}\ndescription: \"Demo: does one thing.\"\n---\n\n{body}"
    (d / "SKILL.md").write_bytes(text.replace("\n", newline).encode("utf-8"))
    return d


class ConvertTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.binding = self.tmp / "binding.md"
        self.binding.write_text("## Host binding\n\n| a | b |\n", encoding="utf-8")
        self.profile = self.tmp / "p.yaml"
        self.profile.write_text("inputs:\n  - name: x\ntools: [t1]\nintegration: {connector: X}\n",
                                encoding="utf-8")

    def run_convert(self, src, **kw):
        return c.convert(src, self.tmp / "out", self.profile, self.binding, **kw)

    def test_body_unchanged_lf_and_crlf(self):
        for nl in ("\n", "\r\n"):
            src = make_skill(self.tmp / nl.encode().hex(), newline=nl)
            r = self.run_convert(src)
            self.assertTrue(r["ok"], r["problems"])
            self.assertTrue(r["body_unchanged"])
            out = (self.tmp / "out" / "demo-skill" / "SKILL.md").read_bytes()
            if nl == "\r\n":
                self.assertEqual(out.count(b"\n"), out.count(b"\r\n"))
            else:
                self.assertNotIn(b"\r\n", out)

    def test_frontmatter_keys(self):
        r = self.run_convert(make_skill(self.tmp))
        self.assertEqual(r["frontmatter_keys"], ["name", "description", "inputs", "tools", "integration"])
        r2 = c.convert(make_skill(self.tmp / "m"), self.tmp / "out2", self.profile, None, minimal=True)
        self.assertEqual(r2["frontmatter_keys"], ["name", "description"])

    def test_missing_reference_fails(self):
        r = self.run_convert(make_skill(self.tmp, with_ref=False))
        self.assertFalse(r["ok"])
        self.assertTrue(any("references/a.md" in p for p in r["problems"]))

    def test_bad_name_fails(self):
        r = self.run_convert(make_skill(self.tmp, name="Bad_Name"))
        self.assertFalse(r["ok"])

    def test_zip_has_skill_md_at_root(self):
        src = make_skill(self.tmp)
        zsrc = self.tmp / "demo-skill.skill"
        with zipfile.ZipFile(zsrc, "w") as z:
            for p in src.rglob("*"):
                if p.is_file():
                    z.write(p, ("demo-skill/" + p.relative_to(src).as_posix()))
        r = self.run_convert(zsrc)
        self.assertTrue(r["ok"], r["problems"])
        with zipfile.ZipFile(self.tmp / "out" / r["zip"]) as z:
            self.assertIn("SKILL.md", z.namelist())
            self.assertIn("references/a.md", z.namelist())
        report = json.loads((self.tmp / "out" / "demo-skill.conversion.json").read_text())
        self.assertEqual(report["file_count"], 2)

    def test_unsafe_zip_rejected(self):
        bad = self.tmp / "bad.zip"
        with zipfile.ZipFile(bad, "w") as z:
            z.writestr("../evil/SKILL.md", "---\nname: x\ndescription: y\n---\n")
        with self.assertRaises(c.ConversionError):
            self.run_convert(bad)


if __name__ == "__main__":
    unittest.main()
