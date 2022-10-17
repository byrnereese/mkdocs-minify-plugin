import fnmatch
import os
import sys
from datetime import datetime, timedelta
from timeit import default_timer as timer

import csscompressor
import jsmin
import mkdocs.structure.files
from htmlmin import minify
from mkdocs import utils as mkdocs_utils
from mkdocs.config import Config, config_options
from mkdocs.plugins import BasePlugin

EXTRAS = {
    "js": "extra_javascript",
    "css": "extra_css",
}

MINIFIERS = {
    "js": jsmin.jsmin,
    "css": csscompressor.compress,
}


def _minified_asset(file_name, file_type):
    return file_name.replace("." + file_type, ".min." + file_type)


class MinifyPlugin(BasePlugin):

    config_scheme = (
        ("minify_html", mkdocs.config.config_options.Type(bool, default=False)),
        ("minify_js", mkdocs.config.config_options.Type(bool, default=False)),
        ("minify_css", mkdocs.config.config_options.Type(bool, default=False)),
        ("js_files", mkdocs.config.config_options.Type((str, list), default=None)),
        ("css_files", mkdocs.config.config_options.Type((str, list), default=None)),
        ("htmlmin_opts", mkdocs.config.config_options.Type((str, dict), default=None)),
    )

    def _minify(self, file_type, config):
        minify_func = MINIFIERS[file_type]
        files = self.config[file_type + "_files"] or []

        if not isinstance(files, list):
            files = [files]
        for file in files:
            # Read file and minify
            fn = config["site_dir"] + "/" + file
            if os.sep != "/":
                fn = fn.replace(os.sep, "/")
            with open(fn, mode="r+", encoding="utf-8") as f:
                minified = minify_func(f.read())
                f.seek(0)
                f.write(minified)
                f.truncate()
            # Rename to .min.{file_type}
            os.rename(fn, _minified_asset(fn, file_type))

    def _minify_extra_config(self, file_type, config):
        """Change extra_ entries so they point to the minified files."""
        files = self.config[file_type + "_files"] or []
        extra = EXTRAS[file_type]

        if not isinstance(files, list):
            files = [files]
        for file in files:
            if file in config[extra]:
                config[extra][config[extra].index(file)] = _minified_asset(file, file_type)
        return config

    def on_post_page(self, output_content, page, config):
        if self.config["minify_html"]:
            opts = self.config["htmlmin_opts"] or {}
            for key in opts:
                if key not in [
                    "remove_comments",
                    "remove_empty_space",
                    "remove_all_empty_space",
                    "reduce_boolean_attributes",
                    "remove_optional_attribute_quotes",
                    "convert_charrefs",
                    "keep_pre",
                    "pre_tags",
                    "pre_attr",
                ]:
                    print("htmlmin option " + key + " not recognized")
            return minify(
                output_content,
                opts.get("remove_comments", False),
                opts.get("remove_empty_space", False),
                opts.get("remove_all_empty_space", False),
                opts.get("reduce_empty_attributes", True),
                opts.get("reduce_boolean_attributes", False),
                opts.get("remove_optional_attribute_quotes", True),
                opts.get("convert_charrefs", True),
                opts.get("keep_pre", False),
                opts.get("pre_tags", ("pre", "textarea")),
                opts.get("pre_attr", "pre"),
            )
        else:
            return output_content

    def on_post_template(self, output_content, template_name, config):
        # Minify HTML template files, e.g., 404.html
        if template_name.endswith(".html"):
            return self.on_post_page(output_content, {}, config)
        else:
            return output_content

    def on_pre_build(self, config):
        if self.config["minify_js"]:
            config = self._minify_extra_config("js", config)
        if self.config["minify_css"]:
            config = self._minify_extra_config("css", config)
        return config

    def on_post_build(self, config):
        if self.config["minify_js"]:
            self._minify("js", config)
        if self.config["minify_css"]:
            self._minify("css", config)
        return config
