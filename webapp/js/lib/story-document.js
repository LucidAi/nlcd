/*
 *
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 *
 */

function MdDocument() {

    // Resize center content;
    var clientBarCenterTopMargin = 70;
    var clientBarCenter = $("#ClientBarCenter");
    clientBarCenter.height($(window).height() - clientBarCenterTopMargin);
    $(window).resize(function() {
        clientBarCenter.height($(window).height() - clientBarCenterTopMargin);
    });

    // Resize left bar views

    // Resize right bar views

    // Init tool-tips
    $("body").tooltip({
        "delay":        1,
        "container":    "body",
        "trigger": "    hover",
        "animation":    true,
        "selector":     ".tip-tooltip"
    });

}
