
import os
import sys
import click
import pkg_resources
from livereload import Server, shell
from . import Yass, publisher
from .yass import PAGE_FORMAT
from .__about__ import *

CWD = os.getcwd()


TPL_HEADER = """
---
title: Page Title
description: Page Description
meta:
    key: value
---

"""

TPL_BODY = {

# JADE
    "jade": """
.row
    .col-md-12.text-center
        h1
            strong.
                {{ page.title }}
        h3.
            Ok Yass!

.row
    .col-md-12
""",

# HTML

    "html": """
<div class=\"row\">
    <div class=\"col-md-12\">
            This is Yass!
    </div>
</div>
""",

# MD
    "md": """

# My markdown Yass!

"""

}


def copy_resource(src, dest):
    """
    To copy package data to destination
    """
    package_name = "yass"
    dest = (dest + "/" + os.path.basename(src)).rstrip("/")
    if pkg_resources.resource_isdir(package_name, src):
        if not os.path.isdir(dest):
            os.makedirs(dest)
        for res in pkg_resources.resource_listdir(__name__, src):
            copy_resource(src + "/" + res, dest)
    else:
        if not os.path.isfile(dest) \
                and os.path.splitext(src)[1] not in [".pyc"]:
            with open(dest, "wb") as f:
                f.write(pkg_resources.resource_string(__name__, src))
        else:
            print("File exists: %s " % dest)


def stamp_yass_current_version(dir):
    f = os.path.join(dir, "yass.yml")
    if os.path.isfile(f):
        with open(f, "r+") as file:
            content = file.read()
            content = content.replace("##VERSION##", __version__)
            file.seek(0)
            file.write(content)
            file.truncate()


def footer():
    print("-" * 80)


def alert(message):
    print("::ALERT::")
    print(message)


def error(message):
    print("::ERROR::")
    print(message)


@click.group()
def cli():
    """
    Yass: Yet Another Static Site (generator)
    """
    pass

@cli.command("version")
def version():
    """Return the vesion of Yass"""
    print(__version__)
    footer()

@cli.command("build")
def build():
    """Build everything"""
    print("Building pages...")
    Yass(CWD).build()
    print("Done!")

    footer()


@cli.command("publish")
@click.argument("endpoint", default="s3")
@click.option("--purge-files", is_flag=True)
@click.option("--rebuild-manifest", is_flag=True)
@click.option("--skip-upload", is_flag=True)
def publish(endpoint, purge_files, rebuild_manifest, skip_upload):
    """Publish the site"""
    print("Publishing site to %s ..." % endpoint.upper())

    yass = Yass(CWD)
    target = endpoint.lower()

    sitename = yass.sitename
    if not sitename:
        raise ValueError("Missing site name")

    endpoint = yass.config.get("hosting.%s" % target)
    if not endpoint:
        raise ValueError("%s endpoint is missing in the config" % target.upper())

    if target == "s3":
        p = publisher.S3Website(sitename=sitename,
                                aws_access_key_id=endpoint.get("aws_access_key_id"),
                                aws_secret_access_key=endpoint.get("aws_secret_access_key"),
                                region=endpoint.get("aws_region"))

        if not p.website_exists:
            print(">>>")
            print("Setting S3 site...")
            if p.create_website() is True:
                p.create_www_website()
                print("New bucket created: %s" % p.sitename)

        if rebuild_manifest:
            print(">>>")
            print("Rebuilding site's manifest...")
            p.create_manifest_from_s3_files()

        if purge_files is True or endpoint.get("purge_files") is True:
            print(">>>")
            print("Purging files...")
            exclude_files = endpoint.get("purge_exclude_files", [])
            p.purge_files(exclude_files=exclude_files)

        if not skip_upload:
            print(">>>")
            print("Uploading your site...")
            p.upload(yass.build_dir)
        else:
            print(">>>")
            print("WARNING: files upload was skipped because of the use of --skip-upload")

        print("")
        print("Yass! Your site has been successfully published to: ")
        print(p.website_endpoint_url)

    footer()



@cli.command("setup-dns")
@click.argument("endpoint", default="s3")
def setup_dns(endpoint):
    """Setup site domain to route to static site"""
    print("Setting up DNS...")

    yass = Yass(CWD)
    target = endpoint.lower()

    sitename = yass.sitename
    if not sitename:
        raise ValueError("Missing site name")

    endpoint = yass.config.get("hosting.%s" % target)
    if not endpoint:
        raise ValueError(
            "%s endpoint is missing in the hosting config" % target.upper())

    if target == "s3":
        p = publisher.S3Website(sitename=sitename,
                                aws_access_key_id=endpoint.get("aws_access_key_id"),
                                aws_secret_access_key=endpoint.get("aws_secret_access_key"),
                                region=endpoint.get("aws_region"))

        print("Setting AWS Route53 for: %s ..." % p.sitename)
        p.setup_dns()
        print("")
        print("Yass! Route53 setup successfully!")
        print("You can now visit the site at :")
        print(p.sitename_endpoint)
    footer()


@cli.command("create-site")
@click.argument("sitename")
def create_site(sitename):
    """Create a new site directory and init Yass"""
    sitepath = os.path.join(CWD, sitename)
    if os.path.isdir(sitepath):
        print("Site directory '%s' exists already!" % sitename)
    else:
        print("Creating site: %s..." % sitename)
        os.makedirs(sitepath)
        copy_resource("skel/", sitepath)
        stamp_yass_current_version(sitepath)
        print("Site created successfully!")
        print("CD into '%s' and run 'yass serve' to view the site" % sitename)

    footer()


@cli.command("init")
def init():
    """Initialize Yass in the current directory """
    yass_conf = os.path.join(CWD, "yass.yml")
    if os.path.isfile(yass_conf):
        print("::ALERT::")
        print("It seems like Yass is already initialized here.")
        print("If it's a mistake, delete 'yass.yml' in this directory")
    else:
        print("Init Yass in %s ..." % CWD)
        copy_resource("skel/", CWD)
        stamp_yass_current_version(CWD)
        print("Yass init successfully!")
        print("Run 'yass serve' to view the site")

    footer()


@cli.command("create-page")
@click.argument("pagename")
def create_page(pagename):
    """ Create a new page Omit the extension, it will create it as .jade file """
    page = pagename.lstrip("/").rstrip("/")
    _, _ext = os.path.splitext(pagename)

    # If the file doesn't have an extension, we'll just create one
    if not _ext or _ext == "":
        page += ".jade"

    if not page.endswith(PAGE_FORMAT):
        error("Can't create '%s'" % page)
        print("Invalid filename format")
        print("Filename must be in: '%s'" % " | ".join(PAGE_FORMAT))
    else:
        engine = Yass(CWD)
        markup = "jade"
        if page.endswith(".md"):
            markup = "md"
        if page.endswith(".html"):
            markup = "html"

        dest_file = os.path.join(engine.pages_dir, page)
        dest_dir = os.path.dirname(dest_file)

        content = TPL_HEADER
        content += TPL_BODY[markup]

        if os.path.isfile(dest_file):
            error("File exists already")
            print("Location: %s" % dest_file)

        else:
            if not os.path.isdir(dest_dir):
                os.makedirs(dest_dir)
            with open(dest_file, "w") as f:
                f.write(content)

            print("New page created: '%s'" % page)
            print("Location: %s" % dest_file)


    footer()

@cli.command()
@click.option("-p", "--port", default=None)
@click.option("--no-livereload", default=None)
@click.option("--open-url", default=None)
def serve(port, no_livereload, open_url):
    """Serve the site """

    engine = Yass(CWD)
    if not port:
        port = engine.config.get("local_server.port", 8000)
    if no_livereload is None:
        no_livereload = True if engine.config.get("local_server.livereload") is False else False
    if open_url is None:
        open_url = False if engine.config.get("local_server.open_url") is False else True

    print("Serving at %s" % port)
    print("Livereload is %s" % ("OFF" if no_livereload else "ON"))

    def build_static():
        engine.build_static()

    def build_pages():
        engine.build_pages()

    engine.build()

    server = Server()
    if no_livereload is False:
        server.watch(engine.static_dir + "/", build_static)
        server.watch(engine.pages_dir + "/", build_pages)
        server.watch(engine.templates_dir + "/", build_pages)
        server.watch(engine.data_dir + "/", build_pages)

    server.serve(open_url_delay=open_url, port=port, root=engine.build_dir)


@cli.command("clean")
def clean():
    """Clean the build dir """
    print("Cleaning build dir...")
    Yass(CWD).clean_build_dir()
    print("Done!")
    footer()


def cmd():
    try:
        print("*" * 80)
        print("=" * 80)
        print("Yass %s!" % __version__)
        print("-" * 80)
        yass_conf = os.path.join(CWD, "yass.yml")
        yass_init = os.path.isfile(yass_conf)
        sys_argv = sys.argv
        exempt_argv = ["init", "create-site", "version"]
        if len(sys_argv) > 1:
            if not yass_init and sys_argv[1] not in exempt_argv:
                error("Yass is not initialized yet in this directory: %s" % CWD)
                print("Run 'yass init' to initialize Yass in the current directory")
                footer()
            else:
                cli()
        else:
            cli()
    except Exception as e:
        print("Ohhh noooooo! Something bad happens")
        print(">> %s " % e)
        raise e

