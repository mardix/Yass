"""
~ Yass ~
"""

import os
import re
import sys
import yaml
import json
import arrow
import shutil
import jinja2
import logging
import frontmatter
import pkg_resources
import webassets.loaders
from slugify import slugify
from extras import (jade, md, macro_tags)
from distutils.dir_util import copy_tree
from webassets import Environment as WAEnv
from webassets.ext.jinja2 import AssetsExtension
from webassets.script import CommandLineEnvironment as WACommandLineEnvironment
from .__about__ import *

# ------------------------------------------------------------------------------

NAME = "Yass"

PAGE_FORMAT = (".html", ".md", ".jade")

DEFAULT_LAYOUT = "layouts/default.jade"


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

# ==============================================================================
# -------------------------------- YASS ----------------------------------------
# ==============================================================================

class Yass(object):

    RE_BLOCK_BODY = re.compile(r'{%\s*block\s+body\s*%}')
    RE_BLOCK_BODY_PARSED = re.compile(r'{%\s*block\s+body\s*%}(.*?){%\s*endblock\s*%}')
    RE_EXTENDS = re.compile(r'{%\s*extends\s+(.*?)\s*%}')

    default_page_meta = {
        "title": "",            # The title of the page
        "markup": None,         # The markup to use. ie: md | jade | html (default)
        "slug": None,           # The pretty url new name of the file. A file with the same name will be created
        "url": "",              # This will be added when processed
        "description": "",      # Page description
        "pretty_url": True,     # By default, all url will be pretty (search engine friendly) Set to False to keep the .html
        "meta": {},
        "layout": None,         # The layout for the page
        "template": None        # The page template.
    }
    tpl_env = None
    _templates = {}
    _pages_meta = {}

    def __init__(self, root_dir):

        self.root_dir = root_dir
        self.build_dir = os.path.join(self.root_dir, "build")
        self.static_dir = os.path.join(self.root_dir, "static")
        self.content_dir = os.path.join(self.root_dir, "content")
        self.pages_dir = os.path.join(self.root_dir, "pages")
        self.templates_dir = os.path.join(self.root_dir, "templates")
        self.data_dir = os.path.join(self.root_dir, "data")
        self.build_static_dir = os.path.join(self.build_dir, "static")

        config_file = os.path.join(self.root_dir, "yass.yml")
        self.config = load_conf(config_file)
        self.default_layout = self.config.get("default_layout", DEFAULT_LAYOUT)

        site_config = self.config.get("site", {})
        site_config.setdefault("base_url", "/")
        self.base_url = site_config.get("base_url")

        self.sitename = self.config.get("sitename")

        if self.sitename:
            self.sitename = self.sitename\
                .lstrip("http://")\
                .lstrip("https://")\
                .lstrip("www.")

        self._init_jinja({
            "site": site_config,
            "data": self._load_data(),
            "__YASS__": self._yass_vars()
        })

        self._init_webassets()

    def _yass_vars(self):
        """ Global variables """
        utc = arrow.utcnow()
        return {
            "NAME": __title__,
            "VERSION": __version__,
            "URL": __uri__,
            "GENERATOR": "%s %s" % (__title__, __version__),
            "YEAR": utc.year
        }

    def _init_jinja(self, global_context={}):

        loader = jinja2.ChoiceLoader([
            # global macros
            jinja2.DictLoader({
                "yass.macros": pkg_resources.resource_string(__name__,
                                                             "extras/macros.html"),
            }),
            jinja2.FileSystemLoader(self.templates_dir)
        ])

        self.tpl_env = jinja2.Environment(loader=loader,
                                          extensions=[
                                              'pyjade.ext.jinja.PyJadeExtension',
                                              'yass.extras.htmlcompress.HTMLCompress',
                                              'yass.extras.jade.JadeTagExtension',
                                              'yass.extras.md.MarkdownExtension',
                                              'yass.extras.md.MarkdownTagExtension',
                                              AssetsExtension
                                          ])

        macro_tags.configure_environment(self.tpl_env, ["yass.macros"])
        self.tpl_env.globals.update(global_context)
        self.tpl_env.filters.update({
            "format_datetime": lambda dt, format: arrow.get(dt).format(format),
            "yass_link_to": self._link_to,  # link for a
            "yass_url_to": self._url_to  # url for a page
        })

    def _get_page_meta(self, page):
        """
        Cache the page meta from the frontmatter and assign new keys
        The cache data will be used to build links or other properties
        """
        meta = self._pages_meta.get(page)
        if not meta:
            src_file = os.path.join(self.pages_dir, page)
            with open(src_file) as f:
                _, _ext = os.path.splitext(src_file)
                markup = _ext.replace(".", "")
                _meta, _ = frontmatter.parse(f.read())
                meta = self.default_page_meta.copy()
                meta["meta"].update(self.config.get("site.meta", {}))
                meta.update(_meta)
                dest_file, url = self._get_dest_file_and_url(page, meta)
                meta["url"] = url
                meta["dest_file"] = dest_file
                if meta.get("markup") is None:
                    meta["markup"] = markup
                self._pages_meta[page] = meta

        return meta

    def _get_page_content(self, page):
        """ Get the page content without the frontmatter """
        src_file = os.path.join(self.pages_dir, page)
        with open(src_file) as f:
            _meta, content = frontmatter.parse(f.read())
            return content

    def _link_to(self, page, text=None, title=None, _class="", id="", alt="", **kwargs):
        """ Build the A HREF LINK To a page."""
        anchor = ""
        if "#" in page:
            page, anchor = page.split("#")
            anchor = "#" + anchor
        meta = self._get_page_meta(page)
        return "<a href='{url}' class='{_class}' id='{id}'  title=\"{title}\">{text}</a>".format(
            url=meta.get("url", "/") + anchor,
            text=text or meta.get("title") or title,
            title=title or "",
            _class=_class,
            id=id
        )

    def _url_to(self, page):
        """ Get the url of a  page """
        anchor = ""
        if "#" in page:
            page, anchor = page.split("#")
            anchor = "#" + anchor
        meta = self._get_page_meta(page)
        return meta.get("url")

    def _get_dest_file_and_url(self, filepath, page_meta={}):
        """ Return tuple of the file destination and url """

        filename = filepath.split("/")[-1]
        filepath_base = filepath.replace(filename, "").rstrip("/")
        slug = page_meta.get("slug")
        fname = slugify(slug) if slug else filename \
            .replace(".html", "") \
            .replace(".md", "") \
            .replace(".jade", "")

        if page_meta.get("pretty_url") is False:
            dest_file = os.path.join(filepath_base, "%s.html" % fname)
        else:
            dest_dir = filepath_base
            if filename not in ["index.html", "index.md", "index.jade"]:
                dest_dir = os.path.join(filepath_base, fname)
            dest_file = os.path.join(dest_dir, "index.html")

        url = "/" + dest_file.replace("index.html", "")
        return dest_file, url

    def _load_data(self):
        """ Load data from the data directory """
        data = {}
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
                            data[name] = _
        return data

    def _init_webassets(self):

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

    def build_static(self):
        """ Build static files """
        if not os.path.isdir(self.build_static_dir):
            os.makedirs(self.build_static_dir)
        copy_tree(self.static_dir, self.build_static_dir)
        if self.webassets_cmd:
            self.webassets_cmd.build()

    def build_pages(self):
        """Iterate over the pages_dir and build the pages """
        for root, _, files in os.walk(self.pages_dir):
            base_dir = root.replace(self.pages_dir, "").lstrip("/")
            if not base_dir.startswith("_"):
                for f in files:
                    src_file = os.path.join(base_dir, f)
                    self._build_page(src_file)

    def _build_page(self, filepath):
        """ To build from filepath, relative to pages_dir """
        filename = filepath.split("/")[-1]
        # If filename starts with _ (underscore) or . (dot) do not build
        if not filename.startswith(("_", ".")) and (filename.endswith(PAGE_FORMAT)):
            meta = self._get_page_meta(filepath)
            content = self._get_page_content(filepath)
            self.create_page(build_dir=self.build_dir,
                             filepath=meta["dest_file"],
                             context={"page": meta},
                             content=content,
                             markup=meta.get("markup"),
                             template=meta.get("template"),
                             layout=meta.get("layout") or self.default_layout
                             )

    def create_page(self, build_dir, filepath, context={}, content=None, template=None, markup=None, layout=None):
        """
        To dynamically create a page and save it in the build_dir
        :param build_dir: (path) The base directory that will hold the created page
        :param filepath: (string) the name of the file to create. May  contain slash to indicate directory
                        It will also create the url based on that name
                        If the filename doesn't end with .html, it will create a subdirectory
                        and create `index.html`
                        If file contains `.html` it will stays as is
                        ie:
                            post/waldo/where-is-waldo/ -> post/waldo/where-is-waldo/index.html
                            another/music/new-rap-song.html -> another/music/new-rap-song.html
                            post/page/5 -> post/page/5/index.html
        :param context: (dict) context data
        :param content: (text) The content of the file to be created. Will be overriden by template
        :param template: (path) if source is not provided, template can be used to create the page.
                         Along with context it allows to create dynamic pages.
                         The file is relative to `/templates/`
                         file can be in html|jade|md
        :param markup: (string: html|jade|md), when using content. To indicate which markup to use.
                        based on the markup it will parse the data
                        html: will render as is
                        jade and md: convert to the appropriate format
        :param layout: (string) when using content. The layout to use.
                        The file location is relative to `/templates/`
                        file can be in html|jade|md
        :return:
        """

        build_dir = build_dir.rstrip("/")
        filepath = filepath.lstrip("/").rstrip("/")
        if not filepath.endswith(".html"):
            filepath += "/index.html"
        dest_file = os.path.join(build_dir, filepath)
        dest_dir = os.path.dirname(dest_file)

        if not os.path.isdir(dest_dir):
            os.makedirs(dest_dir)

        _context = context
        if "page" not in _context:
            _context["page"] = self.default_page_meta.copy()
        if "url" not in _context["page"]:
            _context["page"]["url"] = "/" + filepath.lstrip("/").replace("index.html", "")

        if template:
            if template not in self._templates:
                self._templates[template] = self.tpl_env.get_template(template)
            tpl = self._templates[template]
        else:
            if markup == "md":
                _context["page"]["__toc__"] = md.get_toc(content)
                content = md.convert(content)
            elif markup == "jade":
                content = jade.convert(content)

            # Page must be extended by a layout and have a block 'body'
            # These tags will be included if they are missing
            if re.search(self.RE_EXTENDS, content) is None:
                layout = layout or self.default_layout
                content = "\n{% extends '{}' %} \n\n".replace("{}", layout) + content

            if re.search(self.RE_BLOCK_BODY, content) is None:
                _layout_block = re.search(self.RE_EXTENDS, content).group(0)
                content = content.replace(_layout_block, "")
                content = "\n" + _layout_block + "\n" + \
                          "{% block body %} \n" + content.strip() + "\n{% endblock %}"

            tpl = self.tpl_env.from_string(content)

        with open(dest_file, "w") as fw:
            fw.write(tpl.render(**_context))

    def build(self):
        self.clean_build_dir()
        if not os.path.isdir(self.build_dir):
            os.makedirs(self.build_dir)
        self.build_static()
        self.build_pages()


