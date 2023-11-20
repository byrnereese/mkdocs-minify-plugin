# mkdocs-minify-plugin

[![PyPI - Python Version][python-image]][pypi-link]

An MkDocs plugin to minify HTML, JS or CSS files prior to being written to disk.

HTML minification is done using [htmlmin2](https://github.com/wilhelmer/htmlmin).

JS minification is done using [jsmin](https://github.com/tikitu/jsmin/).

CSS minification is done using [csscompressor](https://github.com/sprymix/csscompressor).

## Setup

Install the plugin using pip:

```bash
pip install mkdocs-minify-plugin
```

Activate the plugin in `mkdocs.yml`:

```yaml
plugins:
  - search
  - minify:
      minify_html: true
      minify_js: true
      minify_css: true
      htmlmin_opts:
          remove_comments: true
      cache_safe: true
      js_files:
          - my/javascript/dir/file1.js
          - my/javascript/dir/file2.js
      css_files:
          - my/css/dir/file1.css
          - my/css/dir/file2.css
```

> **Note:** If you have no `plugins` entry in your config file yet, you'll likely also want to add the `search` plugin. MkDocs enables it by default if there is no `plugins` entry set, but now you have to enable it explicitly.

## Options

- `minify_html`:
  - Defaults to `False`.
  - Sets whether HTML files should be minified.
- `minify_js`:
  - Defaults to `False`.
  - Sets whether JS files should be minified.<br>
    If set to `True`, you must specify the JS to be minified files using `js_files` (see below).
- `minify_css`:
  - Defaults to `False`.
  - Sets whether CSS files should be minified.<br>
    If set to `True`, you must specify the CSS to be minified files using `css_files` (see below).
- `htmlmin_opts`:
  - Defaults to `None`.
  - Sets runtime htmlmin API options using the [config parameters of htmlmin](https://htmlmin.readthedocs.io/en/latest/reference.html#main-functions)
- `cache_safe`:
  - Defaults to `False`.
  - Sets whether a hash should be added to the JS and CSS file names. This ensures that the browser always loads the latest version of the files instead of loading them from the cache.<br>
    If set to `True`, you must specify the files using `js_files` or `css_files` (see below).
- `js_files`:
  - Defaults to `None`.
  - List of JS files to be minified.<br>
    The plugin will generate minified versions of these files and save them as `.min.js` in the output directory.
- `css_files`:
  - Defaults to `None`.
  - List of CSS files to be minified.<br>
    The plugin will generate minified versions of these files and save them as `.min.css` in the output directory.

> **Note:** When using `minify_js` or `minify_css`, you don't have to modify the `extra_javascript` or `extra_css` entries
in your `mkdocs.yml` file. The plugins automatically takes care of that.

[pypi-link]: https://pypi.python.org/pypi/mkdocs-minify-plugin/
[python-image]: https://img.shields.io/pypi/pyversions/mkdocs-minify-plugin?logo=python&logoColor=aaaaaa&labelColor=333333
