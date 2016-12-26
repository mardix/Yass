"""
~ Yass ~
"""

import os
import sys
import re
import shutil
import jinja2
import yaml
import json
import logging
import frontmatter
from distutils.dir_util import copy_tree
import markdown
import pkg_resources
import arrow
from jinja_macro_tags import configure_environment
from webassets.ext.jinja2 import AssetsExtension
from webassets.script import CommandLineEnvironment as WACommandLineEnvironment
from webassets import Environment as WAEnv
import webassets.loaders
import pyjade

# ------------------------------------------------------------------------------

NAME = "Yass"

PAGE_FORMAT = (".html", ".md", ".jade")

DEFAULT_LAYOUT = "layouts/default.html"


# Markdown
mkd = markdown.Markdown(extensions=[
    'markdown.extensions.nl2br',
    'markdown.extensions.sane_lists',
    'markdown.extensions.toc',
    'markdown.extensions.tables'
])


def md_to_html(text):
    """
    Convert MD text to HTML
    :param text:
    :return:
    """
    html = mkd.convert(text)
    mkd.reset()
    return html


def md_get_toc(text):
    """
    Extract Table of Content of MD
    :param text:
    :return:
    """
    mkd.convert(text)
    toc = mkd.toc
    mkd.reset()
    return toc


class dictdot(dict):
    """
    A dict extension that allows dot notation to access the data.
    ie: dict.get('key.key2.0.keyx'). Still can use dict[key1][k2]
    To create: dictdot(my)
    """
    def get(self, key, default=None):
        """ access data via dot notation """
        try:
            val = self
            if "." not in key:
                return self[key]
            for k in key.split('.'):
                if k.isdigit():
                    k = int(k)
                val = val[k]
            return val
        except (TypeError, KeyError, IndexError) as e:
            return default


def load_conf(yml_file):
    with open(yml_file) as f:
        return dictdot(yaml.load(f))


def format_datetime(dt, format):
    return "" if not dt else arrow.get(dt).format(format)


def jade_to_html(text):
    return pyjade.simple_convert(text)


# ==============================================================================
# -------------------------------- YASS ----------------------------------------
# ==============================================================================

class Yass(object):

    RE_BLOCK_TITLE = re.compile(r'{%\s*block\s+title\s*%}')
    RE_BLOCK_TITLE_PARSED = re.compile(r'{%\s*block\s+title\s*%}(.*?){%\s*endblock\s*%}')
    RE_BLOCK_BODY = re.compile(r'{%\s*block\s+body\s*%}')
    RE_BLOCK_BODY_PARSED = re.compile(r'{%\s*block\s+body\s*%}(.*?){%\s*endblock\s*%}')
    RE_EXTENDS = re.compile(r'{%\s*extends\s+(.*?)\s*%}')

    context = {
        "site": {},
        "page": {},
        "data": {}
    }

    default_page_meta = {
        "title": "",  # The title of the page
        "markup": None,  # To switch
        "url": None,  # the url
        "description": None,
        "date": None
    }

    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.build_dir = os.path.join(self.root_dir, ".build")
        self.static_dir = os.path.join(self.root_dir, "static")
        self.content_dir = os.path.join(self.root_dir, "content")
        self.pages_dir = os.path.join(self.root_dir, "pages")
        self.templates_dir = os.path.join(self.root_dir, "templates")
        self.data_dir = os.path.join(self.root_dir, "data")
        self.build_static_dir = os.path.join(self.build_dir, "static")

        config_file = os.path.join(self.root_dir, "yass.yml")
        self.config = load_conf(config_file)
        self.default_layout = self.config.get("default_layout", DEFAULT_LAYOUT)

        # Site context
        self.context["site"] = self.config.get("site", {})

        self.setup()

    def setup(self):
        if not os.path.isdir(self.build_dir):
            os.makedirs(self.build_dir)
        self.setup_jinja()
        self.setup_webassets()

    def setup_jinja(self):
        # Jinja

        loader = jinja2.ChoiceLoader([
            # global macros
            jinja2.DictLoader({
                "yass.macros": pkg_resources.resource_string(__name__,
                                                             "macros.html"),
            }),
            jinja2.FileSystemLoader(self.templates_dir)
        ])

        self.tpl_env = jinja2.Environment(loader=loader,
                                          extensions=['pyjade.ext.jinja.PyJadeExtension',
                                                      AssetsExtension])

        configure_environment(self.tpl_env)
        self.tpl_env.filters.update({
            "format_datetime": format_datetime,
            "markdown_to_html": md_to_html,
            "jade_to_html": jade_to_html
        })
        self.tpl_env.macros.register_from_template('yass.macros')

    def setup_webassets(self):

        assets_env = WAEnv(directory="./static",
                           url=self.config.get("static_url", "/static"))
        bundles = self.config.get("assets_bundles", {})
        assets_env.register(bundles)
        self.tpl_env.assets_environment = assets_env

        self.webassets_cmd = None
        if bundles:
            handler = logging.StreamHandler if self.config.get("debug", False) \
                else logging.NullHandler
            log = logging.getLogger('webassets')
            log.addHandler(handler())
            log.setLevel(logging.DEBUG)
            self.webassets_cmd = WACommandLineEnvironment(assets_env, log)

    def clean_build_dir(self):
        if os.path.isdir(self.build_dir):
            shutil.rmtree(self.build_dir)
        os.makedirs(self.build_dir)

    def load_data(self):
        # Data context
        self.context["data"] = {}
        for root, _, files in os.walk(self.data_dir):
            for fname in files:
                if fname.endswith((".yml", ".json")):
                    name = fname.replace(".yml", "").replace(".json", "")
                    fname = os.path.join(root, fname)
                    if os.path.isfile(fname):
                        with open(fname) as f:
                            _ = {}
                            if fname.endswith(".yml"):
                                _ = yaml.load(f)
                            elif fname.endswith(".json"):
                                _ = json.load(f)
                            self.context["data"][name] = _

    def set_context(self, key, val):
        """
        To programmatically add new context
        :param key:
        :param val:
        :return:
        """
        self.context[key] = val

    def build_static(self):
        """
        Build static assets on demand
        :return:
        """
        if not os.path.isdir(self.build_static_dir):
            os.makedirs(self.build_static_dir)

        copy_tree(self.static_dir, self.build_static_dir)

        if self.webassets_cmd:
            self.webassets_cmd.build()

    def build_pages(self):
        """
        Build all the pages
        :return:
        """
        for root, _, files in os.walk(self.pages_dir):
            base_dir = root.replace(self.pages_dir, "").lstrip("/")
            dest_dir = (self.build_dir + "/" + base_dir).rstrip("/")
            if not base_dir.startswith("_"):
                for f in files:
                    src_file = root + "/" + f
                    self._build_page(dest_dir=dest_dir, src_file=src_file)

    def _build_page(self, src_file, dest_dir):

        filename = src_file.split("/")[-1]

        if not filename.startswith("_") and (filename.endswith(PAGE_FORMAT)):
            dest_dir = dest_dir.rstrip("/")
            metadata = self.default_page_meta.copy()

            with open(src_file) as f:
                _meta, content = frontmatter.parse(f.read())
            metadata.update(_meta)

            if filename in ["index.html", "index.md", "index.jade"]:
                dest_file = dest_dir + "/index.html"
            else:
                fname = filename.replace(".html", "").replace(".md", "").replace(".jade", "")
                dest_dir += "/" + fname
                dest_file = dest_dir + "/index.html"
            if not os.path.isdir(dest_dir):
                os.makedirs(dest_dir)

            if "url" in metadata:
                url = metadata["url"]
            else:
                url = dest_dir.replace(self.build_dir, "")

            # page context
            context = self.context.copy()
            context["page"] = metadata

            if src_file.endswith(".md") or metadata["markup"] == "md":
                context["page"]["__toc__"] = md_get_toc(content)
                content = md_to_html(content)
            elif src_file.endswith(".jade") or metadata["markup"] == "jade":
                content = jade_to_html(content)

            # Page must be extended by a layout and have a block 'body'
            # These tags will be included if they are missing
            # .jade and .md files don't require these tags

            if re.search(self.RE_EXTENDS, content) is None:
                layout = metadata["layout"] if "layout" in metadata else self.default_layout
                content = ("\n{% extends '{}' %} \n\n"
                           .replace("{}", layout)) + content

            if re.search(self.RE_BLOCK_BODY, content) is None:
                _layout_block = re.search(self.RE_EXTENDS, content).group(0)
                content = content.replace(_layout_block, "")
                content = "\n" + _layout_block + "\n" + \
                          "{% block body %} \n" + content.strip() + "\n{% endblock %}"

            tpl = self.tpl_env.from_string(content)
            with open(dest_file, "w") as fw:
                fw.write(tpl.render(context))

    def build(self):
        self.clean_build_dir()
        self.setup()
        self.load_data()
        self.build_static()
        self.build_pages()

