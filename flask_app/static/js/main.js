$(".c").click(function(){
	if($(this).siblings(".active").length == 0){ 

	if ($(this).hasClass("active")){
		$(this).removeClass("active");
		// $(this).css("z-index", '1'); // this seems to help smooth animation out //
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