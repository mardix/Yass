# Yass !

Yet Another Static Site 

https://mardix.github.io/yass

---

Thank you for using Yass! 

## Quickstart

### Create your site

You see this page because you've already created the site, so no need to create 
the site again (yassss!), but for future reference, to create a (another) website, just go 
to the root of all your sites, and type the following 

    yass create YOUR-SITE-NAME
    
    cd YOUR-SITE-NAME


### Developing & Serving

While developing, you will want to see the changes. Run the code below, it will 
allow you to see the changes you make, and will reload whenever you make a change.
    
    yass serve
    

### Build your site

To build your site, run `build`. It will generate all the pages and place them 
inside of `/build` directory. The content in that directory can be published 
to where ever you like.

    yass build 
    
    
### Publish your site

Now your site is built, it's time to publish it, run the `publish`. For now, it 
will attempt to publish it to AWS S3. Soon it will use other providers

If you want to host it somewhere else, just upload the `/build` content 
to where you want it to be

    yass publish 
    
    
### Clean the build directory

There is really no need to keep the generated files inside of the build. So
you can delete them. Because we still have our `/pages` and `/static` folder
 all your content is still available. You'll just have to `yass build` 
 to have the content back in there.

    yass clean
    
    
To learn more, go to https://mardix.github.io/yass
    
    

