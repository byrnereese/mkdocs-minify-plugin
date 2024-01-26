"""
Pytest test file for the `mkdocs_minify_plugin` module.
"""
import hashlib
import shutil
import subprocess
from pathlib import Path
from distutils.dir_util import copy_tree

import pytest

# region fixtures


@pytest.fixture
def extra_dir(tmp_path: Path):
    """Fixture that provides the path to the extra_assets directory after build"""
    return tmp_path / "site" / "extra_assets"


@pytest.fixture
def mkdocs_build(tmp_path: Path):
    """Fixture that builds mkDocs based on the `mkdocs.yml` file"""
    return _build_fixture_base(tmp_path, file_name="mkdocs.yml")


@pytest.fixture
def mkdocs_build_with_extras(tmp_path: Path) -> int:
    """Fixture that builds mkDocs based on the `mkdocs_with_extras.yml` file"""
    return _build_fixture_base(tmp_path, file_name="mkdocs_with_extras.yml")


@pytest.fixture
def mkdocs_build_cache_safe(tmp_path: Path) -> int:
    """Fixture that builds mkDocs based on the `mkdocs_cache_safe.yml` file"""
    return _build_fixture_base(tmp_path, file_name="mkdocs_cache_safe.yml")


@pytest.fixture
def mkdocs_build_cache_safe_minified(tmp_path: Path) -> int:
    """Fixture that builds mkDocs based on the `mkdocs_cache_safe_minified.yml` file"""
    return _build_fixture_base(tmp_path, file_name="mkdocs_cache_safe_minified.yml")


def _build_fixture_base(tmp_path: Path, *, file_name: str) -> int:
    """Base function that handles fixture content creation"""
    fixture_dir: str = str(Path(__file__).parent / "fixtures")
    temp_dir: str = str(tmp_path)

    copy_tree(fixture_dir, temp_dir)
    return subprocess.check_call(["mkdocs", "build", "-f", Path(temp_dir) / file_name])


# endregion

# region tests


def test_build_no_extras(mkdocs_build: int, extra_dir: Path, tmp_path: Path) -> None:
    """Tests that the extra files are minified but, aren't added to the .html files"""
    _assert_minified_css(extra_dir / "css" / "style.min.css")
    _assert_minified_js(extra_dir / "js" / "script.min.js")
    _assert_minified_template_no_extras(
        file_path=tmp_path / "site" / "index.html",
        file_hash="468e45e1d823325ceebfd1c3eaa6e390c9629b43eaefcbdf5ff5d3c77cb358e10737d19d44ab0ad17f66a9935800c135",
    )
    _assert_minified_template_no_extras(
        file_path=tmp_path / "site" / "404.html",
        file_hash="f8ab14b0fc7865c4eabaa9a4ce0c5db191e7b1fb6ca28e450d070847eb3519d2e6cf64c65607245bdc8f414007014c92",
    )


def test_build_with_extras(mkdocs_build_with_extras: int, extra_dir: Path, tmp_path: Path) -> None:
    """Tests that the extra files are minified and are added to the .html files"""
    _assert_minified_css(extra_dir / "css" / "style.min.css")
    _assert_minified_js(extra_dir / "js" / "script.min.js")
    _assert_template_with_extras(
        file_path=tmp_path / "site" / "index.html",
        file_hash="b164f41214bc362faf6a43c57be6c783a276ae188450b9f91ba27d4ffd581426e7e7902c9ce1dc93279f4b0badb92ec1",
    )
    _assert_template_with_extras(
        file_path=tmp_path / "site" / "404.html",
        file_hash="e2dc0e1cc11452d4d1ec5b22a626a36d134b253e7ac8201b57c88b600a0011e262e9c50bd7a57f1b56dfd3eab08b14cf",
    )


def test_build_cache_safe(mkdocs_build_cache_safe: int, extra_dir: Path, tmp_path: Path) -> None:
    """Tests that the extra files aren't minified and are added to the .html files with a hashed name."""
    css_hash_prefix: str = "style.885f1a"
    js_hash_prefix: str = "script.275b9a"

    with open(extra_dir / "css" / f"{css_hash_prefix}.css", encoding="utf8") as file:
        css_data: str = file.read()

    assert (
        hashlib.sha384(css_data.encode("utf8")).hexdigest()
        == "885f1a3f199708ad6f4d170707080d0066bee0bc4a58d8fee73679c6f6880c52b6885eae5fb6c2b9b337d25b339aaf52"
    )

    with open(extra_dir / "js" / f"{js_hash_prefix}.js", encoding="utf8") as file:
        js_data: str = file.read()

    assert (
        hashlib.sha384(js_data.encode("utf8")).hexdigest()
        == "275b9a6166c6648a711c4c2b8a2684b99493da5546bc76c8e30d629fbfe5e656a3a72d689758f029f9acb195a9a1702b"
    )

    _assert_template_with_extras(
        file_path=tmp_path / "site" / "index.html",
        css_prefix=css_hash_prefix,
        js_prefix=js_hash_prefix,
        file_hash="6ae88614660e302573660221fce668fc9cdbadb8fccf1cb1ec4a912d09518d3755773b3d398dbdef97fa9be2bcc6e322",
        minified_extras=False,
        minified_html=False,
    )
    _assert_template_with_extras(
        file_path=tmp_path / "site" / "404.html",
        css_prefix=css_hash_prefix,
        js_prefix=js_hash_prefix,
        file_hash="735db5fb6dcfd9bcc09eb287c6303e8c88d7ce8db71d59c1dbb02e837a83836395b508bfbac43652d530f781761e40fc",
        minified_extras=False,
        minified_html=False,
    )


def test_build_cache_safe_minified(
    mkdocs_build_cache_safe_minified: int, extra_dir: Path, tmp_path: Path
) -> None:
    """Tests that the extra files are minified and are added to the .html files with a hashed name."""
    css_hash_prefix: str = "style.54ca0a"
    js_hash_prefix: str = "script.fda10b"

    _assert_minified_css(extra_dir / "css" / f"{css_hash_prefix}.min.css")
    _assert_minified_js(extra_dir / "js" / f"{js_hash_prefix}.min.js")
    _assert_template_with_extras(
        file_path=tmp_path / "site" / "index.html",
        css_prefix=css_hash_prefix,
        js_prefix=js_hash_prefix,
        file_hash="24ebe25956981b302e11251dd82cd1b58087195a2f5fe2fec57534705a66fbabba233a367f6d1431ce28bd4f6d8c5f85",
    )
    _assert_template_with_extras(
        file_path=tmp_path / "site" / "404.html",
        css_prefix=css_hash_prefix,
        js_prefix=js_hash_prefix,
        file_hash="76f4c03cd62fb3a2af689cddbb1ff1cb32bee269c329c819df462c203e4f74d88adbd227e582ee7305f8b26a226a9187",
    )


# endregion

# region assertion helpers


def _assert_minified_css(file_path: Path) -> None:
    """Asserts the contents of the minified css file and compares the checksum hash"""
    with open(file_path, encoding="utf8") as file:
        minified: str = file.read()

    assert minified == r".ui-hidden{display:none}"
    assert (
        hashlib.sha384(minified.encode("utf8")).hexdigest()
        == "54ca0a60263b2bf48ec6c74bb27ff3bdd000442f73e0b78811a5c097ac1d2b0e7b8fea17fe16f9d9618b76566a3ea171"
    )


def _assert_minified_js(file_path: Path) -> None:
    """Asserts the contents of the minified js file and compares the checksum hash"""
    with open(file_path, encoding="utf8") as file:
        minified: str = file.read()

    assert minified == r"console.log('Hello World');"
    assert (
        hashlib.sha384(minified.encode("utf8")).hexdigest()
        == "fda10b7f2831f8b6121a9f65c809876b4aa52b2fee3a1084a6d101e12e042abf6ff7cf028d557b101e18ff156877b981"
    )


def _assert_minified_template_no_extras(
    *, file_path: Path, css_prefix: str = "style", js_prefix: str = "script", file_hash: str
) -> None:
    """Asserts that the extra files aren't added to the .html files and compares the checksum hash"""
    with open(file_path, encoding="utf8") as file:
        minified: str = file.read()

    assert f"extra_assets/js/{js_prefix}.js" not in minified
    assert f"extra_assets/css/{css_prefix}.css" not in minified
    assert f"extra_assets/js/{js_prefix}.min.js" not in minified
    assert f"extra_assets/css/{css_prefix}.min.css" not in minified
    assert hashlib.sha384(minified.encode("utf8")).hexdigest() == file_hash


def _assert_template_with_extras(
    *,
    file_path: Path,
    css_prefix: str = "style",
    js_prefix: str = "script",
    file_hash: str,
    minified_extras: bool = True,
    minified_html: bool = True,
) -> None:
    """Asserts that the extra files are added to the .html files and compares the checksum hash"""
    with open(file_path, encoding="utf8") as file:
        file_data: str = file.read()

    if not minified_html:
        # remove timestamp comment for constant hash
        file_data = "\n".join(file_data.splitlines()[:-6])

    if minified_extras:
        assert f"extra_assets/js/{js_prefix}.js" not in file_data
        assert f"extra_assets/css/{css_prefix}.css" not in file_data
        assert f"extra_assets/js/{js_prefix}.min.js" in file_data
        assert f"extra_assets/css/{css_prefix}.min.css" in file_data
    else:
        assert f"extra_assets/js/{js_prefix}.js" in file_data
        assert f"extra_assets/css/{css_prefix}.css" in file_data
        assert f"extra_assets/js/{js_prefix}.min.js" not in file_data
        assert f"extra_assets/css/{css_prefix}.min.css" not in file_data

    assert hashlib.sha384(file_data.encode("utf8")).hexdigest() == file_hash


# endregion
