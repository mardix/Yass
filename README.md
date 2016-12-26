
# Yass! 

YASS is Yet Another Static Site (generator). 


A static site generator that makes you say Yass! once done.

Yass is meant to be developer and non developer friendly. 

Yass allows you to write your content in either HTML, Markdown or Jade. 

HTML gives you full independence 

Mardkdown, when writing article 

Jade, when writing HTML in a minimalist form

All three are powered by the powerful Jinja2 template language.


Features:

- Friendly Url
- Deploy to S3
- Jinja
- Jade
- Markdown
- HTML



It helps you create static and deploy to S3.


Technology uses:

    - Jinja2: Powerful templating language
    - Webassets: manages your assets
    - Front Matter, to add context to the page
    - Arrow to write date and time

## Install

    pip install yass
    
    
## Create and serve a new site on local

    cd ~/into-your-dir
    
    yass create mysite.com
    
    cd mysite.com 
    
    yass serve


### To build the content only 

    yass build 
    
    
### To deploy to S3

    yass deploy 
 
deploy will trigger a new build, then deploy the content S3
    
    



---

Structure:

/_build
    |
/assets/
    |
/data/
    |
/pages/
    |
/templates/
    |
    /layouts/

---------

/_build:
    This where the build sites will be created. The content of this dir is ready for upload

/assets:
    Hold the assets static files. This directory will be copied to the _build as is

/data:
    Contains data context to inject in the templates.
    The content can be in YAML or JSON
    To access the data, use the file name as as the namespace -> data.yml -> {{ data.$var }}

/pages:
    Contains all the pages to be built
    If the pages contain local context -> {{ page.title }}


/templates
    Contains all the templates to be included, including layouts and custom.
    If you want to create a file to include, it must be placed in here and be called in the page

/templates/layouts
    Contains all the layouts to use

/template/partials
    Contains custom content to include in the pages

---


## Content:

### Supported format:

Sax support `.html` and `.md` files. It will ignore all other extensions in the `/pages` directory


### Organization:

The pages in Sax should be arranged in the same way they are intended for the rendered website.
Without any additional configuration, the following will just work. Hugo supports content nested at any level.

    /pages
        |
        |- index.html               // <- http://a.com/
        |
        |- about-us.md              // <- http://a.com/about-us
        |
        |- /post
            |
            |- my-awesome-post.html // <- http://a.com/post/my-awesome-post.html


### Front Matter & Page Context

It enables you to include the meta data and context of the content right with it.
It only supports the Yaml format, it is placed on top of the page. 

    ---
    title: My site title
    slug: /a-new-path/
    description: 
    
    ---

Your front matter data get parsed as a local object, ie: {{ page.title }}

You can also include your own context



## Macros

This macro is autoaded (thanks to jinja-macro-tags) and can use HTML like
tag to load the macros below:
ie:

{{ img(src='tdyhs.png') }}

can now be written in html like:

<m:img src="tdhd.png" />

or jinja like

<{img src='jfhf.png'}/>

We recommend the HTML like instead.



## TODO
Pagination 
RSS