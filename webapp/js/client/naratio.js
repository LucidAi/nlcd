/*
 *
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 *
 */


function Narratio(story_graph) {

    this.sg = story_graph;
    this.items = [];
    this.activated = [];

}


Narratio.prototype.Find = function(textQuery, extraAttrib) {

};


function NarratioEntity(eId, eName, eExtraAttrib) {

    this.name = name;
    this.extraAttrib = eExtraAttrib;

    this.isSelected = false;
    this.isRelated = false;

    this.refArticles = 0;
    this.refAuthors = 0;
    this.refSources = 0;

}