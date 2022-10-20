import hashlib
import os
import sys
import fnmatch
from timeit import default_timer as timer
from datetime import datetime, timedelta

from mkdocs import utils as mkdocs_utils
from mkdocs.config import config_options, Config
from mkdocs.plugins import BasePlugin
import mkdocs.structure.files

import csscompressor
import jsmin
from htmlmin import minify


EXTRAS = {
    "js": "extra_javascript",
    "css": "extra_css",
}
MINIFIERS = {
    "js": jsmin.jsmin,
    "css": csscompressor.compress
}


def _minified_asset(minify_flag, file_name, file_type, file_hash):
    """Adds [.hash].min. text to the asset file name."""
    hash_part: str = f".{file_hash[:6]}" if file_hash else ""
    min_part: str = ".min" if minify_flag else ""
    return file_name.replace(f".{file_type}", f"{hash_part}{min_part}.{file_type}")


class MinifyPlugin(BasePlugin):

    config_scheme = (
        ('minify_html', mkdocs.config.config_options.Type(bool, default=False)),
        ('minify_js', mkdocs.config.config_options.Type(bool, default=False)),
        ('minify_css', mkdocs.config.config_options.Type(bool, default=False)),
        ('js_files', mkdocs.config.config_options.Type((str, list), default=None)),
        ('css_files', mkdocs.config.config_options.Type((str, list), default=None)),
        ('htmlmin_opts', mkdocs.config.config_options.Type((str, dict), default=None)),
        ('cache_safe', mkdocs.config.config_options.Type(bool, default=False)),
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
        files = self.config[file_type + '_files'] or []
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

    def _minify_extra_config(self, file_type, config):
        """Changes extra_ entries, so they point to the minified/hashed file names."""
        files = self.config[file_type + '_files'] or []
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

                config[extra][config[extra].index(file)] = _minified_asset(minify_flag, file, file_type, file_hash)
        return config

    def on_post_page(self, output_content, page, config):
        if self.config['minify_html']:
            opts = self.config['htmlmin_opts'] or {}
            for key in opts:
                if key not in ['remove_comments','remove_empty_space','remove_all_empty_space','reduce_boolean_attributes','remove_optional_attribute_quotes','convert_charrefs','keep_pre','pre_tags','pre_attr']:
                    print("htmlmin option " + key + " not recognized")
            return minify(output_content, opts.get("remove_comments", False), opts.get("remove_empty_space", False), opts.get("remove_all_empty_space", False), opts.get("reduce_empty_attributes", True), opts.get("reduce_boolean_attributes", False), opts.get("remove_optional_attribute_quotes", True), opts.get("convert_charrefs", True), opts.get("keep_pre", False), opts.get("pre_tags", ('pre', 'textarea')), opts.get("pre_attr", 'pre'))
        else:
            return output_content

    def on_post_template(self, output_content, template_name, config):
        # Minify HTML template files, e.g., 404.html
        if template_name.endswith(".html"):
            return self.on_post_page(output_content, {}, config)
        else:
            return output_content

    def on_pre_build(self, config):
        if self.config['minify_js'] or self.config["cache_safe"]:
            config = self._minify_extra_config('js', config)
        if self.config['minify_css'] or self.config["cache_safe"]:
            config = self._minify_extra_config('css', config)
        return config

    def on_post_build(self, config):
        if self.config['minify_js'] or self.config["cache_safe"]:
            self._minify('js', config)
        if self.config['minify_css'] or self.config["cache_safe"]:
            self._minify('css', config)
        return config
