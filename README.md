
# Yass! 

YASS is Yet Another Static Site (generator). 



### About 

A static site generator that makes you say Yass!

Yass is created out of frustration of not finding a simple enough, flexible
static site generator, that supports HTML, but also Markdown and Jinja, and 
Jade.

It's either you use markdown all the way, or you don't get nothing. 

Well, Yass is here!


### Philosophy

Yass is meant to be simple and straight forward. From configuration, to setting up 
pages, Yass provides non-developers, designers and developers a tool that will do one 
thing and one thing only: generate a static site. 


### Technology

Yass is built in Python, and features the powerful templating language Jinja2. 

Yass allows you to write your content in either Jade, Mardkdown or plain HTML. 

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
    
    
### To publish to S3

    yass deploy 
 
deploy will trigger a new build, then deploy the content S3
    
   

---

Structure:

    ____
        |
        /build
            |
        /static/
            |
        /data/
            |
        /pages/
            |
        /templates/
            |
            /layouts/

---------

/build: This where the build sites will be created. The content of this dir is ready for upload

/static: Hold the assets static files. This directory will be copied to the `build` as is

/data:
    Contains JSON data context to inject in the templates.
    To access the data, use the file name as as the namespace -> data.json -> {{ data.$var }}

/pages:
    Contains all the pages to be built
    If the pages contain local context -> {{ page.title }}


/templates:
    Contains all the templates to be included, including layouts and custom.
    If you want to create a file to include, it must be placed in here and be called in the page

/templates/layouts
    Contains all the layouts to use

/template/partials
    Contains custom content to include in the pages

---


## Content:

### Supported format:

Yass support `.jade`, `.html` and `.md` files. It will ignore all other extensions in the `/pages` directory

Files starting with `_` (underscore) will be ignored


### Organization:

The pages in Yass should be arranged in the same way they are intended for the rendered website.
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


# Advanced

## Data Driven

In addition to data files, you can load a resource from any api endpoint. 

The data returned must be in the json format.



## Generators

To generate pages dynamically from a data source

##### context

Generators return a `context` key in the page variable. 

For `single` type, the context is the data for that page

For `pagination` type, the context is a list (array) of data chunk

##### paginator

Generators returns `paginator` key in the page variable, if the `type` is 'pagination'

`pagination` contains: `total_pages`, `current_pages`, `page_slug`, `index_slug`


### Generator: Single

Generate single pages from a source containing list (array) of data

    ---
    
    _generator:
        type: single
        data_source: posts
        slug: /
    ---

`data_source`:  Dot notation can be use to 
 access other node of the data: ie: 
 
    // data/posts.json
    
    {
        "all": [
            {},
            ...
        ],
        "archived": [
            {},
            ...
        ]
    }

You can access the data as:
    
    data_source: posts.archived


`slug`: Will dynamically build the slug. Having the `slug` will overwrite the 
data slug if it has one. 

`slug` format based on the data, so data token must be provided 

ie: `/{post_type}/{id}/{post_slug}`

### Generator: Pagination

Will generated a paginated 

    ---
    
    _generator:
        type: pagination
        data_source: posts
        per_page: 20
        limit: 100
        slug: /all/page/{page_num}
        index_slug: /all
    ---




## TODO
 
RSS