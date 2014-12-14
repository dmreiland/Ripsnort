/*!
 * Start Bootstrap - Freelancer Bootstrap Theme (http://startbootstrap.com)
 * Code licensed under the Apache License v2.0.
 * For details, see http://www.apache.org/licenses/LICENSE-2.0.
 */

// jQuery for page scrolling feature - requires jQuery Easing plugin
$(function() {
    $('.page-scroll a').bind('click', function(event) {
        var $anchor = $(this);
        $('html, body').stop().animate({
            scrollTop: $($anchor.attr('href')).offset().top
        }, 1500, 'easeInOutExpo');
        event.preventDefault();
    });
});

$(document).ready(function()
{
// set the initial offset +100 to hide most of the intro icon
//     $(window).scrollTop(100);

	$('#intro_img').transition({y:'-400px'});

    setTimeout(function()
    {
		$('#intro_img').transition({
			y: '+=400px',
			rotate: '+=270deg',
			opacity: 1.0,
		}, 500, 'ease');
    }, 1000);


    /* Can't insert curly braces from post. Post process tags and add after */
    $(".highlight,.stringsub").each( function(index,value)
    {
        var existingHtml = $(value).html();
        var newHtml = existingHtml.replace(/CURLYOPEN/g,'{')
        						  .replace(/CURLYCLOSE/g,'}')
        						  .replace(/STRSTAR/g,'*');
        
        $(value).html( newHtml );
    });
});

var isNavBarVisible = false;

$(window).scroll(function()
{
    var scrollOffset = $(window).scrollTop();
    var isOnFirstPage = ( scrollOffset > 550 );
    
    if ( isOnFirstPage &&  !isNavBarVisible )
    {
        isNavBarVisible = true;
		$('.navbar').animate({"opacity": 1})    
    }
    else if ( !isOnFirstPage &&  isNavBarVisible )
    {
        isNavBarVisible = false;
		$('.navbar').animate({"opacity": 0})
    }
    
    var topOffset = (scrollOffset * -2.1);
    topOffset -= 400;
    $('.img-responsive').css({top: topOffset + 'px'});
});

// Highlight the top nav as scrolling occurs
$('body').scrollspy({
    target: '.navbar-fixed-top'
})

// Closes the Responsive Menu on Menu Item Click
$('.navbar-collapse ul li a').click(function() {
    $('.navbar-toggle:visible').click();
});
