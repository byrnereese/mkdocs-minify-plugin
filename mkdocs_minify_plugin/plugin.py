import hashlib
import os
from typing import Dict, Optional, Tuple, Union

import csscompressor
import htmlmin
import jsmin
import mkdocs.config.config_options
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin
from mkdocs.structure.pages import Page

EXTRAS = {
    "js": "extra_javascript",
    "css": "extra_css",
}

MINIFIERS = {
    "js": jsmin.jsmin,
    "css": csscompressor.compress,
}


def _minified_asset(minify_flag, file_name, file_type, file_hash):
    """Adds [.hash].min. text to the asset file name."""
    hash_part: str = f".{file_hash[:6]}" if file_hash else ""
    min_part: str = ".min" if minify_flag else ""
    return file_name.replace(f".{file_type}", f"{hash_part}{min_part}.{file_type}")


class MinifyPlugin(BasePlugin):

    config_scheme = (
        ("minify_html", mkdocs.config.config_options.Type(bool, default=False)),
        ("minify_js", mkdocs.config.config_options.Type(bool, default=False)),
        ("minify_css", mkdocs.config.config_options.Type(bool, default=False)),
        ("js_files", mkdocs.config.config_options.Type((str, list), default=None)),
        ("css_files", mkdocs.config.config_options.Type((str, list), default=None)),
        ("htmlmin_opts", mkdocs.config.config_options.Type((str, dict), default=None)),
        ("cache_safe", mkdocs.config.config_options.Type(bool, default=False)),
    )

    path_to_hash = {}
    """
    The file hash is stored in a dict, so that it's generated only once.
    Relevant only when `on_pre_build` is run AND `cache_safe` is `True`.
    """

    path_to_data = {}
    """
    The file data is stored in a dict, so that it's read only once.
    Relevant only when `on_pre_build` is run AND `cache_safe` is `True`.
    """

    def _minify(self, file_type, config):
        minify_func = MINIFIERS[file_type]
        files = self.config[file_type + "_files"] or []
        minify_flag = self.config[f"minify_{file_type}"]

        if not isinstance(files, list):
            files = [files]
        for file in files:
            # Read file and minify
            fn = f"{config['site_dir']}/{file}".replace("\\", "/")
            with open(fn, mode="r+", encoding="utf-8") as f:
                if self.config["cache_safe"]:
                    f.write(self.path_to_data[file])
                else:
                    minified = minify_func(f.read())
                    f.seek(0)
                    f.write(minified)
                f.truncate()

            file_hash = self.path_to_hash.get(file, "")

            # Rename to [.hash].min.{file_type}
            os.rename(fn, _minified_asset(minify_flag, fn, file_type, file_hash))

    def _minify_html_page(self, output: str) -> Optional[str]:
        """Minifies html page content."""
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

    def _minify_extra_config(self, file_type, config):
        """Changes extra_ entries, so they point to the minified/hashed file names."""
        files = self.config[file_type + "_files"] or []
        extra = EXTRAS[file_type]
        minify_func = MINIFIERS[file_type]
        minify_flag = self.config[f"minify_{file_type}"]

        if not isinstance(files, list):
            files = [files]
        for file in files:
            if file in config[extra]:

                file_hash = ""

                # When `cache_safe`, the hash is needed before the build,
                # so it's generated from the data from the docs source file
                if self.config["cache_safe"]:
                    docs_file_path = f"{config['docs_dir']}/{file}".replace("\\", "/")

                    with open(docs_file_path, encoding="utf8") as f:
                        file_data = f.read()

                        if minify_flag:
                            file_data = minify_func(file_data)

                        # store data for use in `on_post_build`
                        self.path_to_data[file] = file_data

                    file_hash = hashlib.sha384(file_data.encode("utf8")).hexdigest()
                    # store hash for use in `on_post_build`
                    self.path_to_hash[file] = file_hash

                config[extra][config[extra].index(file)] = _minified_asset(
                    minify_flag, file, file_type, file_hash
                )
        return config

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

    def on_pre_build(self, config):
        if self.config["minify_js"] or self.config["cache_safe"]:
            config = self._minify_extra_config("js", config)
        if self.config["minify_css"] or self.config["cache_safe"]:
            config = self._minify_extra_config("css", config)
        return config

    def on_post_build(self, config):
        if self.config["minify_js"] or self.config["cache_safe"]:
            self._minify("js", config)
        if self.config["minify_css"] or self.config["cache_safe"]:
            self._minify("css", config)
        return config
