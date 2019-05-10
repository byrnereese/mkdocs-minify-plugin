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
        ('minify_js', mkdocs.config.config_options.Type(bool, default=False)),
        ('js_files', mkdocs.config.config_options.Type((str, list), default=None))
    )

    def __init__(self):
        self.enabled = True
        self.total_time = 0

    def on_post_page(self, output_content, page, config):
        if self.config['minify_html']:
            return minify(output_content)
        else:
            return output_content

    def on_files(self, files, config):
        if self.config['minify_js']:
            jsfiles = self.config['js_files'] or []
            if not isinstance(jsfiles, list):
                jsfiles = [jsfiles]
            out = []
            
            def isinjsfiles(name):
                for jsfile in jsfiles:
                    if fnmatch.fnmatchcase(name, jsfile):
                        return True
                return False
            
            for f in files:
                name = f.src_path
                docs_dir = config['docs_dir']
                # Windows reports filenames as eg. a\\b\\c instead of a/b/c
                if os.sep != '/':
                    name = name.replace(os.sep, '/')
                    docs_dir = docs_dir.replace(os.sep, '/')
                if isinjsfiles(name):
                    input_filename = docs_dir + '/' + name
                    output_filename = input_filename.replace('.js','.min.js')
                    minified = ''
                    # Read input file and minify
                    with open(input_filename) as inputfile:
                        minified = jsmin(inputfile.read())
                    # Write minified output file
                    with open(output_filename, 'w') as outputfile:
                        outputfile.write(minified)
                    # Adapt file object properties 
                    f.src_path = f.src_path.replace('.js', '.min.js')
                    f.abs_src_path = f.abs_src_path.replace('.js', '.min.js')
                    f.dest_path = f.dest_path.replace('.js', '.min.js')
                    f.abs_dest_path = f.abs_dest_path.replace('.js', '.min.js')
                    f.url = f.url.replace('.js', '.min.js')
                out.append(f)
            return mkdocs.structure.files.Files(out)
        else:
            return files
    
    def on_post_build(self, config):
        if self.config['minify_js']:
            # Remove minified files from docs_dir
            jsfiles = self.config['js_files'] or []
            if not isinstance(jsfiles, list):
                jsfiles = [jsfiles]
            docs_dir = config['docs_dir']
            if os.sep != '/':
                docs_dir = docs_dir.replace(os.sep, '/')
            for jsfile in jsfiles:
                os.remove(docs_dir + "/" + jsfile.replace('.js', '.min.js'))
        return config

    def on_pre_build(self, config):
        if self.config['minify_js']:
            # Change extra_javascript entries so they point to the minified files
            jsfiles = self.config['js_files'] or []
            if not isinstance(jsfiles, list):
                jsfiles = [jsfiles]
            for jsfile in jsfiles:
                if jsfile in config['extra_javascript']:
                    config['extra_javascript'][config['extra_javascript'].index(jsfile)] = jsfile.replace('.js', '.min.js')
        return config
