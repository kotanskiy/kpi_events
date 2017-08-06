/**
 * Created by Admin on 16.07.2017.
 */
function footer() {
    if ($(document).height() <= $(window).height()){
        $("footer.footer").addClass("navbar-fixed-bottom");
    }else {
        $("footer.footer").removeClass("navbar-fixed-bottom");
    }
}
footer();
setInterval('footer()', 500);




