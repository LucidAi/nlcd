/*
 *
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 *
 */

function TableAPI () {

    this.sort = {

        articleR:   false,
        articleP:   "name",

        sourceR:    false,
        sourceP:    "name",

        authorR:    false,
        authorP:    "name"

    };

}

TableAPI.prototype.OrderBy = function(table, predicate) {
    if (this.sort[table + "P"] == predicate) {
        this.sort[table + "R"] = !this.sort[table + "R"];
    }
    this.sort[table + "P"] = predicate;
};

TableAPI.prototype.textFilter = function(actual, expected) {
    console.log([actual, expected]);
    return true;
};


function StoryLayout() {

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

    // Init table API functions
    this.tableAPI = new TableAPI();

}
