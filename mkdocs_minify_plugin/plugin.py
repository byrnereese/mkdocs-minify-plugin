import os
import sys
import fnmatch
from timeit import default_timer as timer
from datetime import datetime, timedelta

from mkdocs import utils as mkdocs_utils
from mkdocs.config import config_options, Config
from mkdocs.plugins import BasePlugin
import mkdocs.structure.files

from jsmin import jsmin
from htmlmin import minify

class MinifyPlugin(BasePlugin):

    config_scheme = (
        ('minify_html', mkdocs.config.config_options.Type(bool, default=False)),
        ('htmlmin_opts', mkdocs.config.config_options.Type((str, dict), default=None)),
        ('minify_js', mkdocs.config.config_options.Type(bool, default=False)),
        ('js_files', mkdocs.config.config_options.Type((str, list), default=None))
    )

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
        if self.config['minify_js']:
            jsfiles = self.config['js_files'] or []
            if not isinstance(jsfiles, list):
                jsfiles = [jsfiles]
            for jsfile in jsfiles:
                # Change extra_javascript entries so they point to the minified files
                if jsfile in config['extra_javascript']:
                    config['extra_javascript'][config['extra_javascript'].index(jsfile)] = jsfile.replace('.js', '.min.js')
        return config

    def on_post_build(self, config):
        if self.config['minify_js']:
            jsfiles = self.config['js_files'] or []
            if not isinstance(jsfiles, list):
                jsfiles = [jsfiles]
            for jsfile in jsfiles:
                # Read JS file and minify
                fn = config['site_dir'] + '/' + jsfile
                if os.sep != '/':
                    fn = fn.replace(os.sep, '/')
                with open(fn, mode="r+", encoding="utf-8") as f:
                    minified = jsmin(f.read())
                    f.seek(0)
                    f.write(minified)
                    f.truncate()
                # Rename to .min.js
                os.rename(fn, fn.replace('.js','.min.js'))
        return config
