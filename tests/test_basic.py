import distutils.dir_util
import hashlib
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def extra_dir(tmp_path):
    return tmp_path / "site" / "extra_assets"


@pytest.fixture
def mkdocs_build(tmp_path):
    return _build_fixture_base(tmp_path, file_name="mkdocs.yml")


@pytest.fixture
def mkdocs_build_with_extras(tmp_path):
    return _build_fixture_base(tmp_path, file_name="mkdocs_with_extras.yml")


def _build_fixture_base(tmp_path, *, file_name):
    fixture_dir = str(Path(__file__).parent / "fixtures")
    temp_dir = str(tmp_path)

    distutils.dir_util.copy_tree(fixture_dir, temp_dir)
    return subprocess.check_call(["mkdocs", "build", "-f", Path(temp_dir) / file_name])


def test_build_no_extras(mkdocs_build, extra_dir, tmp_path):
    _assert_minified_css(extra_dir / "css" / "style.min.css")
    _assert_minified_js(extra_dir / "js" / "script.min.js")
    _assert_minified_template_no_extras(
        file_path=tmp_path / "site" / "index.html",
        file_hash="544b92316ee6219418120cfc0347f6f1b996f93833287777345da06a38f5f05e374d87a1a35e6bee96508169262d8f97",
    )
    _assert_minified_template_no_extras(
        file_path=tmp_path / "site" / "404.html",
        file_hash="91b1fdfb1b0eb78a20992da953b22f4a72b86336bcf7845cd976b5e4a84337b1bdedab7a09f869d9cab80fcb3bd872dc",
    )


def test_build_with_extras(mkdocs_build_with_extras, extra_dir, tmp_path):
    _assert_minified_css(extra_dir / "css" / "style.min.css")
    _assert_minified_js(extra_dir / "js" / "script.min.js")
    _assert_minified_template_with_extras(
        file_path=tmp_path / "site" / "index.html",
        file_hash="c102275d47fb49aeda0c2e35c35daf5da1ef5ce96f5360cf329578dc65e70b53249b20017b77bcc2516f672917d75762",
    )
    _assert_minified_template_with_extras(
        file_path=tmp_path / "site" / "404.html",
        file_hash="e4d3e614fa3a73e6c0b4231d443009a2bfa3fcbd5f548b19b58222d04fcd4c5dadf702904952b7ea3f1cc124d3904c77",
    )


def _assert_minified_css(file_path):
    with open(file_path) as f:
        minified = f.read()

    assert minified == r".ui-hidden{display:none}"
    assert (
        hashlib.sha384(minified.encode("utf8")).hexdigest()
        == "54ca0a60263b2bf48ec6c74bb27ff3bdd000442f73e0b78811a5c097ac1d2b0e7b8fea17fe16f9d9618b76566a3ea171"
    )


def _assert_minified_js(file_path):
    with open(file_path) as f:
        minified = f.read()

    assert minified == r"console.log('Hello World');"
    assert (
        hashlib.sha384(minified.encode("utf8")).hexdigest()
        == "fda10b7f2831f8b6121a9f65c809876b4aa52b2fee3a1084a6d101e12e042abf6ff7cf028d557b101e18ff156877b981"
    )


def _assert_minified_template_no_extras(
    *, file_path, css_prefix="style", js_prefix="script", file_hash
):
    with open(file_path) as f:
        minified = f.read()

    assert f"extra_assets/js/{js_prefix}.js" not in minified
    assert f"extra_assets/css/{css_prefix}.css" not in minified
    assert f"extra_assets/js/{js_prefix}.min.js" not in minified
    assert f"extra_assets/css/{css_prefix}.min.css" not in minified
    assert hashlib.sha384(minified.encode("utf8")).hexdigest() == file_hash


def _assert_minified_template_with_extras(
    *, file_path, css_prefix="style", js_prefix="script", file_hash
):
    with open(file_path) as f:
        minified = f.read()

    assert f"extra_assets/js/{js_prefix}.js" not in minified
    assert f"extra_assets/css/{css_prefix}.css" not in minified
    assert f"extra_assets/js/{js_prefix}.min.js" in minified
    assert f"extra_assets/css/{css_prefix}.min.css" in minified
    assert hashlib.sha384(minified.encode("utf8")).hexdigest() == file_hash
