import hashlib
import os
from typing import Union

import csscompressor
import htmlmin
import jsmin
import mkdocs.config.config_options
from mkdocs.plugins import BasePlugin

EXTRAS = {
    "js": "extra_javascript",
    "css": "extra_css",
}

MINIFIERS = {
    "js": jsmin.jsmin,
    "css": csscompressor.compress,
}


class MinifyPlugin(BasePlugin):

    config_scheme = (
        ("minify_html", mkdocs.config.config_options.Type(bool, default=False)),
        ("minify_js", mkdocs.config.config_options.Type(bool, default=False)),
        ("minify_css", mkdocs.config.config_options.Type(bool, default=False)),
        ("js_files", mkdocs.config.config_options.Type(Union[str, list], default=None)),
        ("css_files", mkdocs.config.config_options.Type(Union[str, list], default=None)),
        ("htmlmin_opts", mkdocs.config.config_options.Type(Union[str, dict], default=None)),
        ("cache_safe_extras", mkdocs.config.config_options.Type(bool, default=False)),
    )

    path_to_hash = {}
    """
    The file hash is stored in a dict, so that it's generated only once.  
    Relevant only when `on_pre_build` is run AND `cache_safe_extras` is `True`.  
    """

    path_to_data = {}
    """
    The file data is stored in a dict, so that it's read only once.  
    Relevant only when `on_pre_build` is run AND `cache_safe_extras` is `True`.  
    """

    def on_pre_build(self, config):
        """Modify extra file names."""
        if self.config["minify_js"] or self.config["cache_safe_extras"]:
            self._process_config_pre_build("js", config)
        if self.config["minify_css"] or self.config["cache_safe_extras"]:
            self._process_config_pre_build("css", config)

    def on_post_template(self, output_content, template_name, config):
        """Minify HTML template files, e.g. 404.html, before saving to disc."""
        if template_name.endswith(".html"):
            return self._minify_html_page(output_content)
        else:
            return output_content

    def on_post_page(self, output_content, page, config):
        """Minify HTML page before saving to disc."""
        return self._minify_html_page(output_content)

    def on_post_build(self, config):
        """Minify extras before saving to disc."""
        if self.config["minify_js"] or self.config["cache_safe_extras"]:
            self._minify_extra("js", config)
        if self.config["minify_css"] or self.config["cache_safe_extras"]:
            self._minify_extra("css", config)

    def _process_config_pre_build(self, file_type, config):
        """Changes extra_ entries, so they point to the minified/hashed file names."""
        files_to_minify = self.config[f"{file_type}_files"] or []
        minify_func = MINIFIERS[file_type]
        minify_flag = self.config[f"minify_{file_type}"]
        extra = EXTRAS[file_type]

        if not isinstance(files_to_minify, list):
            files_to_minify = [files_to_minify]

        for i, file in enumerate(config[extra]):
            if file not in files_to_minify:
                continue

            file_hash = ""

            # When `cache_safe_extras`, the hash is needed before the build,
            # so it's generated from the data from the docs source file
            if self.config["cache_safe_extras"]:
                file_name = f"{config['docs_dir']}/{file}".replace("\\", "/")

                with open(file_name, encoding="utf8") as f:
                    if minify_flag:
                        file_data: str = minify_func(f.read())
                    else:
                        file_data: str = f.read()
                    self.path_to_data[file] = file_data

                file_hash = hashlib.sha384(file_data.encode("utf8")).hexdigest()
                self.path_to_hash[file] = file_hash

            config[extra][i] = self._minified_asset_name(file, file_type, file_hash)

    def _minified_asset_name(self, file_name, file_type, file_hash):
        """Adds [.hash].min. text to the asset file name."""
        hash_part = f".{file_hash[:6]}" if file_hash else ""
        min_part = ".min" if self.config[f"minify_{file_type}"] else ""
        return file_name.replace(f".{file_type}", f"{hash_part}{min_part}.{file_type}")

    def _minify_html_page(self, output_content):
        """Minifies html page content."""
        if not self.config["minify_html"]:
            return output_content

        output_opts = {
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

        selected_opts = self.config["htmlmin_opts"] or {}

        for key in selected_opts:
            if key in output_opts:
                output_opts[key] = selected_opts[key]
            else:
                print(f"htmlmin option '{key}' not recognized")

        return htmlmin.minify(output_content, **output_opts)

    def _minify_extra(self, file_type, config):
        """Saves the minified extra files."""
        minify_func = MINIFIERS[file_type]
        files = self.config[f"{file_type}_files"] or []

        if not isinstance(files, list):
            files = [files]

        for file in files:
            # Read file and minify
            file_name = f"{config['site_dir']}/{file}".replace("\\", "/")

            with open(file_name, mode="r+", encoding="utf8") as f:
                if self.config["cache_safe_extras"]:
                    f.write(self.path_to_data[file])
                else:
                    minified = minify_func(f.read())
                    f.seek(0)
                    f.write(minified)
                f.truncate()

            file_hash = self.path_to_hash.get(file, "")

            # Rename to [.hash].min.{file_type}
            os.rename(file_name, self._minified_asset_name(file_name, file_type, file_hash))
