$( document ).ready(function() {

	/* recommendation grid animation */
	$(".c").click(function(){
		if($(this).siblings(".active").length == 0){ 

		if ($(this).hasClass("active")){
			$(this).removeClass("active");
			$(this).css("z-index", '1'); // this seems to help smooth animation out //
			$(this).children(".overlay").removeClass("active");
			$(this).children().children(".overlay-info").removeClass("active");
		}
		else {
			$(this).addClass("active");
			$(this).children(".overlay").addClass("active");
			$(this).children().children(".overlay-info").addClass("active");
		}
		
		}
	});

	/* make autocomplete div same width as user input */
	$(".ui-autocomplete").width(document.getElementById("username_input").offsetWidth);


	/* scroll on nav-link click */
	var offset = $("nav")[0].offsetHeight + 20; /* offset by navbar height plus some padding */ 

	/* toggle nav-link color */
	$('.nav-link').click(function(event) {
		event.preventDefault();
		$(window).scrollTop($($(this).attr('href')).offset().top - offset);
		$(".nav-link.active").toggleClass("active");
		$(this).toggleClass("active");
	});
});