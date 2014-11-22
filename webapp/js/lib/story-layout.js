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

    this.clientBarCenterTopMargin = 70;
    this.clientBarCenter = $("#ClientBarCenter");

    // Init tool-tips
    $("body").tooltip({
        "delay"         : 1,
        "container"     : "body",
        "trigger"       : "hover",
        "animation"     : true,
        "selector"      : ".tip-tooltip"
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
