
/**
 * YASS-COMMON
 * Common
 */

$(function(){

    // TIME AGO
    $("time.timeago").timeago();

    
    // OEMBED
    $(".oembed").each(function() {
        var el = $(this);
        var maxWidth = el.data("max-width") || "100%"
        var maxHeight = el.data("max-height") || "480";
        el.oembed(null, {
            includeHandle: false,
            maxWidth: maxWidth,
            maxHeight: maxHeight
        })
    })

})