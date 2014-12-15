/*
 *
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 *
 */

function TableAPI () {

    this.sort = {

        articleR:   true,
        articleP:   "isRelated",

        sourceR:    true,
        sourceP:    "isRelated",

        authorR:    true,
        authorP:    "isRelated"

    };

}

TableAPI.prototype.OrderBy = function(table, predicate, alwaysTrue) {
    if (this.sort[table + "P"] == predicate) {
        this.sort[table + "R"] = !this.sort[table + "R"];
    }
    if (Boolean(alwaysTrue))
        this.sort[table + "R"] = true;
    this.sort[table + "P"] = predicate;
};

TableAPI.prototype.textFilter = function(actual, expected) {
    console.log([actual, expected]);
    return true;
};


function StoryLayout() {

    // Resize center content;

    this.clientBarCenterTopMargin = 70;
    this.clientBarCenter = $("#ClientBarCenter");

    // Init tool-tips
    $("body").tooltip({
        "delay"         : {"show": 0, "hide": 0 },
        "container"     : "body",
        "trigger"       : "hover",
        "animation"     : true,
        "selector"      : ".tip-tooltip"
    });

    // Init pop-overs
    $("body").popover({
        "delay"         : {"show": 0, "hide": 0},
        "container"     : "body",
        "trigger"       : "hover",
        "animation"     : true,
        "html"          : true,
        "selector"      : ".pop-over"
    });

    // Init table API functions
    this.tableAPI = new TableAPI();

    // Components to resize.
    this.components = [];
    this.leftComponents = $("#LeftBar .Component");
    this.rightComponents = $("#RightBar .Component");
    this.leftMargin = 36 + 8 * 2 + 48;
    this.rightMargin = 78 + 8 * 2 + 48;

    var layout = this;

    $(window).resize(function() {
        layout.ResizeContainers();
        layout.RenderComponents();
    });
}


StoryLayout.prototype.ResizeContainers = function () {
    var windowHeight = $(window).height();
    var leftMargin = this.leftMargin;
    var rightMargin = this.rightMargin;
    this.leftComponents.each(function() {
        $(this).height((windowHeight - leftMargin) / 3);
    });
    this.rightComponents.each(function() {
        $(this).height((windowHeight - rightMargin) / 3);
    });
};


StoryLayout.prototype.RenderComponents = function() {
    var windowHeight = $(window).height();
    var windowWidth = $(window).width();
    this.clientBarCenter.height(windowHeight - this.clientBarCenterTopMargin);
    for (var i in this.components) {
        var resizeComponent = this.components[i];
        resizeComponent(windowHeight, windowWidth);
    }
};


StoryLayout.prototype.AddComponent = function (component, placeId, widthFunc, heightFunc) {
    var place = $("#" + placeId);
    this.components.push(function (wW, wH) {
        var pW = place.width();
        var pH = place.height();
        var width = widthFunc(wW, pW);
        var height = heightFunc(wH, pH);
        component.Resize(placeId, place, width, height);
    });
};


StoryLayout.prototype.Date2Str = d3.time.format("%b %d, %Y");
