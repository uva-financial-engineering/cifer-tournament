/* global $, _, Backbone, AUTHENTICATED, STOCKS, INFO */
(function() {
"use strict";

var Entry = Backbone.Model.extend({});

var EntryView = Backbone.View.extend({
  tagName: "tr",
  defaults: {
    liquid: 1
  },
  initialize: function() {
    _.bindAll(this, "render");
  },
  events: {
    click: function() {
      if (this.model.get("liquid") === 1) {
        this.model.get("app").set({selectedEntry: this.model});
      }
    }
  },
  render: function() {
    if (AUTHENTICATED) {
      this.$el.addClass((this.model.get("liquid") === 1) ? "liquid" : "illiquid");
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

var Table = Backbone.Collection.extend({model: Entry});

var App = Backbone.Model.extend({
  defaults: {
    selectedEntry: null
  },
  initialize: function() {
    this.on("change:selectedEntry", function(model) {
      var selectedEntry = model.get("selectedEntry");

      $(".trade-table input, .trade-table button").prop("disabled", false);
      $("#trade_qty").val("").focus();
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
        liquid: INFO[i][5],
        shares: INFO[i][6],
        value: INFO[i][7],
        app: this.model
      }));
    }
    this.model.set({
      table: new Table(entries)
    });
    this.render();
  },
  render: function() {
    // Render asset table
    var infotable = $(".info-table").eq(0);
    for (var i = 0; i < this.model.get("table").length; ++i) {
      var entryView = new EntryView({
        model: this.model.get("table").models[i]
      });
      infotable.append(entryView.render().el);
    }

    if (AUTHENTICATED) {
      // Render transaction error graph
      var r = Raphael("holder", 220, 120);
      var lines = r.linechart(0, 0, 200, 120, TERRORS[0], TERRORS[2], { nostroke: false, axis: "0 0 0 0", symbol: "circle", smooth: true }).hoverColumn(function() {
        $("#terror-info").html(TERRORS[1][this.axis] + ": " + this.values[0]);
      }, function() {
        $("#terror-info").html("&nbsp;");
      }).symbols.attr({ r: 3 });
    }
  }
});

new AppView({model: new App()});

}());
