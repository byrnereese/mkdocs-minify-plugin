"""
A MkDocs plugin to minify HTML, JS or CSS files prior to being written to disk
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
    """Custom plugin class"""

    config_scheme: Tuple = (
        ("minify_html", mkdocs.config.config_options.Type(bool, default=False)),
        ("minify_js", mkdocs.config.config_options.Type(bool, default=False)),
        ("minify_css", mkdocs.config.config_options.Type(bool, default=False)),
        ("js_files", mkdocs.config.config_options.Type((str, list), default=None)),
        ("css_files", mkdocs.config.config_options.Type((str, list), default=None)),
        ("htmlmin_opts", mkdocs.config.config_options.Type((str, dict), default=None)),
        ("cache_safe_extras", mkdocs.config.config_options.Type(bool, default=False)),
    )

    path_to_hash: Dict[str, str] = {}
    """
    The file hash is stored in a dict, so that it's generated only once.
    Relevant only when `on_pre_build` is run AND `cache_safe_extras` is `True`.
    """

    path_to_data: Dict[str, str] = {}
    """
    The file data is stored in a dict, so that it's read only once.
    Relevant only when `on_pre_build` is run AND `cache_safe_extras` is `True`.
    """

    def on_pre_build(self, *, config: MkDocsConfig) -> None:
        """Modify extra file names."""
        if self.config["minify_js"] or self.config["cache_safe_extras"]:
            self._process_config_pre_build("js", config)
        if self.config["minify_css"] or self.config["cache_safe_extras"]:
            self._process_config_pre_build("css", config)

    def on_post_template(
        self, output_content: str, *, template_name: str, config: MkDocsConfig
    ) -> Optional[str]:
        """Minify HTML template files, e.g. 404.html, before saving to disc."""
        if template_name.endswith(".html"):
            return self._minify_html_page(output_content)

        return output_content

    def on_post_page(self, output: str, *, page: Page, config: MkDocsConfig) -> Optional[str]:
        """Minify HTML page before saving to disc."""
        return self._minify_html_page(output)

    def on_post_build(self, *, config: MkDocsConfig) -> None:
        """Minify extras before saving to disc."""
        if self.config["minify_js"] or self.config["cache_safe_extras"]:
            self._minify_extra("js", config)
        if self.config["minify_css"] or self.config["cache_safe_extras"]:
            self._minify_extra("css", config)

    def _process_config_pre_build(self, file_type: str, config: MkDocsConfig) -> None:
        """Changes extra_ entries, so they point to the minified/hashed file names."""
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

            # When `cache_safe_extras`, the hash is needed before the build,
            # so it's generated from the data from the docs source file
            if self.config["cache_safe_extras"]:
                docs_file_path: str = f"{config['docs_dir']}/{file_path}".replace("\\", "/")

                with open(docs_file_path, encoding="utf8") as file:
                    file_data: str = file.read()

                    if minify_flag:
                        file_data = minify_func(file_data)

                    self.path_to_data[file_path] = file_data

                file_hash = hashlib.sha384(file_data.encode("utf8")).hexdigest()
                self.path_to_hash[file_path] = file_hash

            config[extra][i] = self._minified_asset_name(file_path, file_type, file_hash)

    def _minified_asset_name(self, file_name: str, file_type: str, file_hash: str) -> str:
        """Adds [.hash].min. text to the asset file name."""
        hash_part: str = f".{file_hash[:6]}" if file_hash else ""
        min_part: str = ".min" if self.config[f"minify_{file_type}"] else ""
        return file_name.replace(f".{file_type}", f"{hash_part}{min_part}.{file_type}")

    def _minify_html_page(self, output_content: str) -> Optional[str]:
        """Minifies html page content."""
        if not self.config["minify_html"]:
            return output_content

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

        selected_opts: Dict[str, Union[bool, str, Tuple[str, ...]]] = (
            self.config["htmlmin_opts"] or {}
        )

        for key in selected_opts:
            if key in output_opts:
                output_opts[key] = selected_opts[key]
            else:
                print(f"htmlmin option '{key}' not recognized")

        return htmlmin.minify(output_content, **output_opts)

    def _minify_extra(self, file_type: str, config: MkDocsConfig) -> None:
        """Saves the minified extra files."""
        minify_func: Callable = MINIFIERS[file_type]
        file_paths: Union[str, List[str]] = self.config[f"{file_type}_files"] or []

        if not isinstance(file_paths, list):
            file_paths = [file_paths]

        for file_path in file_paths:
            # Read file and minify
            site_file_path: str = f"{config['site_dir']}/{file_path}".replace("\\", "/")

            with open(site_file_path, mode="r+", encoding="utf8") as file:
                if self.config["cache_safe_extras"]:
                    file.write(self.path_to_data[file_path])
                else:
                    minified: str = minify_func(file.read())
                    file.seek(0)
                    file.write(minified)
                file.truncate()

            file_hash: str = self.path_to_hash.get(file_path, "")

            # Rename to [.hash].min.{file_type}
            os.rename(
                site_file_path, self._minified_asset_name(site_file_path, file_type, file_hash)
            )
