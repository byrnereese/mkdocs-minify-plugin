"""
An MkDocs plugin to minify HTML, JS or CSS files prior to being written to disk
"""
import hashlib
import os
from typing import Callable, Dict, List, Optional, Tuple, Union

import csscompressor
import htmlmin
import jsmin
import mkdocs.config.config_options
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin
from mkdocs.structure.pages import Page

EXTRAS: Dict[str, str] = {
    "js": "extra_javascript",
    "css": "extra_css",
}

MINIFIERS: Dict[str, Callable] = {
    "js": jsmin.jsmin,
    "css": csscompressor.compress,
}


class MinifyPlugin(BasePlugin):
    """Custom minify plugin class"""

    config_scheme: Tuple = (
        ("minify_html", mkdocs.config.config_options.Type(bool, default=False)),
        ("minify_js", mkdocs.config.config_options.Type(bool, default=False)),
        ("minify_css", mkdocs.config.config_options.Type(bool, default=False)),
        ("js_files", mkdocs.config.config_options.Type((str, list), default=None)),
        ("css_files", mkdocs.config.config_options.Type((str, list), default=None)),
        ("htmlmin_opts", mkdocs.config.config_options.Type((str, dict), default=None)),
        ("cache_safe", mkdocs.config.config_options.Type(bool, default=False)),
    )

    path_to_hash: Dict[str, str] = {}
    """
    The file hash is stored in a dict, so that it's generated only once.
    Relevant only when `on_pre_build` is run AND `cache_safe` is `True`.
    """

    path_to_data: Dict[str, str] = {}
    """
    The file data is stored in a dict, so that it's read only once.
    Relevant only when `on_pre_build` is run AND `cache_safe` is `True`.
    """

    def _minified_asset(self, file_name: str, file_type: str, file_hash: str) -> str:
        """Add [.hash].min. text to the asset file name."""
        hash_part: str = f".{file_hash[:6]}" if file_hash else ""
        min_part: str = ".min" if self.config[f"minify_{file_type}"] else ""
        return file_name.replace(f".{file_type}", f"{hash_part}{min_part}.{file_type}")

    def _minify(self, file_type: str, config: MkDocsConfig) -> None:
        """Process extras and save them to disk."""
        minify_func: Callable = MINIFIERS[file_type]
        file_paths: Union[str, List[str]] = self.config[f"{file_type}_files"] or []

        if not isinstance(file_paths, list):
            file_paths = [file_paths]

        for file_path in file_paths:
            site_file_path: str = f"{config['site_dir']}/{file_path}".replace("\\", "/")

            with open(site_file_path, mode="r+", encoding="utf8") as file:
                if self.config["cache_safe"]:
                    file.write(self.path_to_data[file_path])
                else:
                    minified: str = minify_func(file.read())
                    file.seek(0)
                    file.write(minified)
                file.truncate()

            file_hash: str = self.path_to_hash.get(file_path, "")

            # Rename to [.hash].min.{file_type}
            os.rename(site_file_path, self._minified_asset(site_file_path, file_type, file_hash))

    def _minify_html_page(self, output: str) -> Optional[str]:
        """Minify HTML page content."""
        if not self.config["minify_html"]:
            return output

        output_opts: Dict[str, Union[bool, str, Tuple[str, ...]]] = {
            "remove_comments": False,
            "remove_empty_space": False,
            "remove_all_empty_space": False,
            "reduce_empty_attributes": True,
            "reduce_boolean_attributes": False,
            "remove_optional_attribute_quotes": True,
            "convert_charrefs": True,
            "keep_pre": False,
            "pre_tags": ("pre", "textarea"),
            "pre_attr": "pre",
        }

        selected_opts: Dict = self.config["htmlmin_opts"] or {}

        for key in selected_opts:
            if key in output_opts:
                output_opts[key] = selected_opts[key]
            else:
                print(f"htmlmin option '{key}' not recognized")

        return htmlmin.minify(output, **output_opts)

    def _minify_extra_config(self, file_type: str, config: MkDocsConfig) -> None:
        """Change extra_ entries, so they point to the minified/hashed file names."""
        files_to_minify: Union[str, List[str]] = self.config[f"{file_type}_files"] or []
        minify_func: Callable = MINIFIERS[file_type]
        minify_flag: bool = self.config[f"minify_{file_type}"]
        extra: str = EXTRAS[file_type]

        if not isinstance(files_to_minify, list):
            files_to_minify = [files_to_minify]

        for i, file_path in enumerate(config[extra]):
            if file_path not in files_to_minify:
                continue

            file_hash: str = ""

            # When `cache_safe`, the hash is needed before the build,
            # so it's generated from the data from the docs source file
            if self.config["cache_safe"]:
                docs_file_path: str = f"{config['docs_dir']}/{file_path}".replace("\\", "/")

                with open(docs_file_path, encoding="utf8") as file:
                    file_data: str = file.read()

                    if minify_flag:
                        file_data = minify_func(file_data)

                    # store data for use in `on_post_build`
                    self.path_to_data[file_path] = file_data

                file_hash = hashlib.sha384(file_data.encode("utf8")).hexdigest()
                # store hash for use in `on_post_build`
                self.path_to_hash[file_path] = file_hash

            config[extra][i] = self._minified_asset(file_path, file_type, file_hash)

    def on_post_page(self, output: str, *, page: Page, config: MkDocsConfig) -> Optional[str]:
        """Minify HTML page before saving to disk."""
        return self._minify_html_page(output)

    def on_post_template(
        self, output_content: str, *, template_name: str, config: MkDocsConfig
    ) -> Optional[str]:
        """Minify HTML template files, e.g. 404.html, before saving to disk."""
        if template_name.endswith(".html"):
            return self._minify_html_page(output_content)

        return output_content

    def on_pre_build(self, *, config: MkDocsConfig) -> None:
        """Process file names of extras in the config."""
        if self.config["minify_js"] or self.config["cache_safe"]:
            self._minify_extra_config("js", config)
        if self.config["minify_css"] or self.config["cache_safe"]:
            self._minify_extra_config("css", config)

    def on_post_build(self, *, config: MkDocsConfig) -> None:
        """Process extras before saving to disk."""
        if self.config["minify_js"] or self.config["cache_safe"]:
            self._minify("js", config)
        if self.config["minify_css"] or self.config["cache_safe"]:
            self._minify("css", config)
