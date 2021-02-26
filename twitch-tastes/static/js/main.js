$( document ).ready(function() {

	/* recommendation grid animation */
	$(".c").click(function(){
		/* prevent clicking other .c elements during animation */
		if ($(this).siblings(".active").length == 0) { 
			$(this).toggleClass("active");
			$(this).children(".overlay").toggleClass("active");
			$(this).children().children(".overlay-info").toggleClass("active");
		} 
		/* prevent clicking same .c element during animation */
		$(this).addClass('freeze');
		$(this).children(".overlay").addClass('freeze');
		$(this).children().children(".overlay-info").addClass('freeze');

	});
	/* remove freeze class on animation end */
	$(".c").on('transitionend webkitTransitionEnd oTransitionEnd MSTransitionEnd', function() {
		$(this).removeClass('freeze');
		$(this).children(".overlay").removeClass('freeze');
		$(this).children().children(".overlay-info").removeClass('freeze');
		$(this).children().children(".overlay-info").css("cursor","pointer"); /* cursor will not revert to pointer unless this is added */
	});

	/* make autocomplete div same width as user input */
	$(".ui-autocomplete").width(document.getElementById("username_input").offsetWidth);


	/* ---------------- NAV-LINK SCROLL BEHAVIOR (CUSTOM SCROLLSPY ) ----------- */
	var offset = $("nav")[0].offsetHeight + 20; /* offset by navbar height plus some padding */ 
	var sections = $(".nav-link").map(function(){return $(this).attr("href")}).get();
	var heights = sections.map(x => $(x).offset().top);
	var prevSection = sections[ heights.map(ht => ht - offset <= window.pageYOffset).lastIndexOf(true) ];
	$(".nav-link[href='" +  prevSection + "']").toggleClass("active");

	$(window).on("scroll", function(){
		var currentSectionIndex = heights.map(ht => ht - offset <= window.pageYOffset).lastIndexOf(true);
		var currentSection = sections[ currentSectionIndex ];
		if (prevSection!=currentSection) {
			$(".nav-link.active").toggleClass("active");
			$(".nav-link[href='" +  currentSection + "']").toggleClass("active");
			prevSection = currentSection;
		}
	});

	/* nav-link click behavior */
	$('.nav-link').click(function(event) {
		event.preventDefault();
		$(window).scrollTop($($(this).attr('href')).offset().top - offset);
	});

	
});