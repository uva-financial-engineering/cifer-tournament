/* global $, _, Backbone, INFO, STOCKS */
(function() {
"use strict";

var Entry = Backbone.Model.extend({
});

var EntryView = Backbone.View.extend({
  tagName: "tr",
  initialize: function() {
    _.bindAll(this, "render");
  },
  events: {
    click: function() {
      this.model.get("app").set({selectedEntry: this.model});
    }
  },
  render: function() {
    if (AUTHENTICATED) {
      this.$el.addClass("entry");
      this.$el.html("<td>" +
        this.model.get("symbol") +
        "</td><td>" +
        this.model.get("sector") +
        "</td><td>" +
        this.model.get("security_name") +
        "</td><td>" +
        this.model.get("bid") +
        "</td><td>" +
        this.model.get("ask") +
        "</td><td>" +
        this.model.get("shares") +
        "</td><td>" +
        this.model.get("value") +
        "</td>");
    } else {
      this.$el.html("<td>" +
        this.model.get("symbol") +
        "</td><td>" +
        this.model.get("sector") +
        "</td><td>" +
        this.model.get("security_name") +
        "</td><td>" +
        this.model.get("bid") +
        "</td><td>" +
        this.model.get("ask") +
        "</td>");
    }
    return this;
  }
});

var Table = Backbone.Collection.extend({
  model: Entry
});

var App = Backbone.Model.extend({
  defaults: {
    selectedEntry: null
  },
  initialize: function() {
    this.on("change:selectedEntry", function(model) {
      var selectedEntry = model.get("selectedEntry");

      $(".trade-table input, .trade-table button").prop("disabled", false);
      $("#trade_qty input").val("");
      $("#trade_asset_name").html(selectedEntry.get("symbol") + " " + selectedEntry.get("security_name"));
      $("#trade_asset").val(selectedEntry.get("security") + "," + selectedEntry.get("strike") + "," + selectedEntry.get("stock_id"));
      $("label[for=trade_position-1]").html((selectedEntry.get("shares") > 0) ? "Sell" : "Short sell");
    });
  }
});

var AppView = Backbone.View.extend({
  el: $(document),
  initialize: function() {
    _.bindAll(this, "render");

    $(".trade-table input, .trade-table button").prop("disabled", true);
    $(".left-sidebar").scrollToFixed();

    var entries = [];
    for (var i = 0; i < INFO.length; ++i) {
      var security_name;
      switch (INFO[i][1]) {
        case 1:
          security_name = INFO[i][2] + "-Call";
          break;
        case 2:
          security_name = INFO[i][2] + "-Put";
          break;
        default:
          security_name = "Stock";
          break;
      }

      entries.push(new Entry({
        stock_id: INFO[i][0],
        symbol: STOCKS[INFO[i][0] - 1][0],
        sector: STOCKS[INFO[i][0] - 1][1],
        security: INFO[i][1],
        security_name: security_name,
        strike: INFO[i][2],
        bid: INFO[i][3],
        ask: INFO[i][4],
        shares: INFO[i][5],
        value: INFO[i][6],
        app: this.model
      }));
    }
    this.model.set({
      table: new Table(entries)
    });
    this.render();
  },
  render: function() {
    var infotable = $(".info-table").eq(0);
    for (var i = 0; i < this.model.get("table").length; ++i) {
      var entryView = new EntryView({
        model: this.model.get("table").models[i]
      });
      infotable.append(entryView.render().el);
    }
  }
});

new AppView({model: new App()});

}());
