from distutils.dir_util import copy_tree
from pathlib import Path
from subprocess import check_call

import pytest


@pytest.fixture
def extra_dir(tmp_path):
    return tmp_path / "site" / "extra_assets"


@pytest.fixture
def mkdocs_build(tmp_path):
    fixture_dir = str(Path(__file__).parent / "fixtures")
    temp_dir = str(tmp_path)

    copy_tree(fixture_dir, temp_dir)
    return check_call(["mkdocs", "build", "-f", f"{temp_dir}/mkdocs.yml"])


def test_css_is_minified(mkdocs_build, extra_dir):
    with open(extra_dir / "css" / "style.min.css", "r") as f:
        minified = f.read()

    assert minified == r".ui-hidden{display:none}"


def test_js_is_minifed(mkdocs_build, extra_dir):
    with open(extra_dir / "js" / "script.min.js", "r") as f:
        minifed = f.read()

    assert minifed == r"console.log('Hello World');"
