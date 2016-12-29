
import os
import pkg_resources
import click
from livereload import Server, shell
from . import Yass, publisher

CWD = os.getcwd()


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

def footer():
    print("-" * 80)

@click.group()
def cli():
    """
    Yass: Static site generator for us!
    """
    pass


@cli.command("build")
def build():
    """Build everything"""
    print("Building pages...")
    Yass(CWD).build()
    print("Done!")

    footer()


@cli.command("publish")
@click.argument("endpoint", default="s3")
def publish(endpoint):
    """Publish the site"""
    print("Publishing site to %s ..." % endpoint.upper())

    yass = Yass(CWD)
    target = endpoint.lower()

    sitename = yass.sitename
    if not sitename:
        raise ValueError("Missing site name")

    endpoint = yass.config.get("publish_endpoints.%s" % target)
    if not endpoint:
        raise ValueError("%s endpoint is missing in the config" % target.upper())

    if target == "s3":
        p = publisher.S3Website(sitename=sitename,
                                aws_access_key_id=endpoint.get("aws_access_key_id"),
                                aws_secret_access_key=endpoint.get("aws_secret_access_key"),
                                region=endpoint.get("aws_region"))

        if not p.website_exists:
            print("Setting S3 site...")
            if p.create_website() is True:
                p.create_www_website()
                print("New bucket created: %s" % p.sitename)

        print("Uploading pages and static files...")
        p.upload(yass.build_dir)

        print("")
        print("Yass! Your site has been successfully published to: ")
        print(p.website_endpoint_url)

    footer()


@cli.command("create")
@click.argument("sitename")
def create(sitename):
    """Create a new site."""
    sitepath = os.path.join(CWD, sitename)
    if os.path.isdir(sitepath):
        print("Site directory '%s' exists already!" % sitename)
    else:
        print("Creating site: %s..." % sitename)
        os.makedirs(sitepath)
        copy_resource("skel/", sitepath)
        print("Site created successfully!")
        print("CD into '%s' and run 'yass serve' to view the site" % sitename)

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
        print("=" * 80)
        print("Yass!")
        print("-" * 80)
        cli()
    except Exception as e:
        print("Ohhh noooooo! Something bad happens")
        print(">> %s " % e)
        raise e

