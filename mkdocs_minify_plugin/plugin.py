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
    )

    def on_pre_build(self, config):
        """Modify extra file names."""
        if self.config["minify_js"]:
            self._minify_extra_config("js", config)
        if self.config["minify_css"]:
            self._minify_extra_config("css", config)

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
        if self.config["minify_js"]:
            self._minify_extra("js", config)
        if self.config["minify_css"]:
            self._minify_extra("css", config)

    def _minify_extra_config(self, file_type, config):
        """Changes extra_ entries, so they point to the minified files."""
        files_to_minify = self.config[f"{file_type}_files"] or []
        extra = EXTRAS[file_type]

        if not isinstance(files_to_minify, list):
            files_to_minify = [files_to_minify]

        for i, file in enumerate(config[extra]):
            if file in files_to_minify:
                config[extra][i] = self._minified_asset_name(file, file_type)

    @staticmethod
    def _minified_asset_name(file_name, file_type):
        """Adds .min. text to the asset file name."""
        return file_name.replace(f".{file_type}", f".min.{file_type}")

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
        """Minifies the extra files."""
        minify_func = MINIFIERS[file_type]
        files = self.config[f"{file_type}_files"] or []

        if not isinstance(files, list):
            files = [files]

        for file in files:
            # Read file and minify
            file_name = f"{config['site_dir']}/{file}".replace("\\", "/")

            with open(file_name, mode="r+", encoding="utf-8") as f:
                minified = minify_func(f.read())
                f.seek(0)
                f.write(minified)
                f.truncate()

            # Rename to .min.{file_type}
            os.rename(file_name, self._minified_asset_name(file_name, file_type))
