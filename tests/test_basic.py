from distutils.dir_util import copy_tree
from hashlib import sha384
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
    return check_call(["mkdocs", "build", "-f", Path(temp_dir) / "mkdocs.yml"])


def test_css_is_minified(mkdocs_build, extra_dir):
    with open(extra_dir / "css" / "style.min.css") as f:
        minified = f.read()

    assert minified == r".ui-hidden{display:none}"
    assert (
        sha384(minified.encode("utf8")).hexdigest()
        == "54ca0a60263b2bf48ec6c74bb27ff3bdd000442f73e0b78811a5c097ac1d2b0e7b8fea17fe16f9d9618b76566a3ea171"
    )


def test_js_is_minifed(mkdocs_build, extra_dir):
    with open(extra_dir / "js" / "script.min.js") as f:
        minified = f.read()

    assert minified == r"console.log('Hello World');"
    assert (
        sha384(minified.encode("utf8")).hexdigest()
        == "fda10b7f2831f8b6121a9f65c809876b4aa52b2fee3a1084a6d101e12e042abf6ff7cf028d557b101e18ff156877b981"
    )


def test_index_is_minifed(mkdocs_build, tmp_path):
    with open(tmp_path / "site" / "index.html") as f:
        minified = f.read()

    assert (
        sha384(minified.encode("utf8")).hexdigest()
        == "544b92316ee6219418120cfc0347f6f1b996f93833287777345da06a38f5f05e374d87a1a35e6bee96508169262d8f97"
    )


def test_404_is_minifed(mkdocs_build, tmp_path):
    with open(tmp_path / "site" / "404.html") as f:
        minified = f.read()

    assert (
        sha384(minified.encode("utf8")).hexdigest()
        == "91b1fdfb1b0eb78a20992da953b22f4a72b86336bcf7845cd976b5e4a84337b1bdedab7a09f869d9cab80fcb3bd872dc"
    )
