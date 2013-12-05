/* global $, _, Backbone, Raphael, AUTHENTICATED, PORTFOLIO, STOCKS, OPTIONS, TRANSACTIONS, CUMTERROR, TERRORS */
(function() {
"use strict";

function securityName(stock_id, security, strike) {
  var security_name = STOCKS[stock_id - 1][0] + " ";
  switch (security) {
    case 1:
      security_name += strike + "-Call";
      break;
    case 2:
      security_name += strike + "-Put";
      break;
    default:
      security_name += "Stock";
      break;
  }
  return security_name;
}

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
      if (this.model.get("liquid") === 1 && AUTHENTICATED) {
        this.model.get("app").set({selectedEntry: this.model});
      }
    }
  }
});

var PortfolioEntryView = EntryView.extend({
  render: function() {
    if (AUTHENTICATED) {
      this.$el.addClass((this.model.get("liquid") === 1) ? "liquid" : "illiquid");
    }
    this.$el.html("<td>" +
      this.model.get("symbol") +
      "</td><td>" +
      this.model.get("security_name") +
      "</td><td>" +
      this.model.get("shares") +
      "</td><td>" +
      this.model.get("value") +
      "</td>");
    return this;
  }
});

var StockEntryView = EntryView.extend({
  render: function() {
    if (AUTHENTICATED) {
      this.$el.addClass((this.model.get("liquid") === 1) ? "liquid" : "illiquid");
    }
    this.$el.html("<td>" +
      this.model.get("symbol") +
      "</td><td>" +
      this.model.get("sector") +
      "</td><td>" +
      this.model.get("bid") +
      "</td><td>" +
      this.model.get("ask") +
      "</td>");
    return this;
  }
});

var OptionEntryView = EntryView.extend({
  render: function() {
    if (AUTHENTICATED) {
      this.$el.addClass((this.model.get("liquid") === 1) ? "liquid" : "illiquid");
    }
    this.$el.html("<td>" +
      this.model.get("symbol") +
      "</td><td>" +
      (this.model.get("security") === 1 ? "Call" : "Put") +
      "</td><td>" +
      this.model.get("strike") +
      "</td><td>" +
      this.model.get("bid") +
      "</td><td>" +
      this.model.get("ask") +
      "</td>");
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
      $("#trade_asset_name").html(selectedEntry.get("security_name"));
      $("#trade_security").val(selectedEntry.get("security"));
      $("#trade_strike").val(selectedEntry.get("strike"));
      $("#trade_stock_id").val(selectedEntry.get("stock_id"));
      $("label[for=trade_position-1]").html((selectedEntry.get("shares") > 0) ? "Sell" : "Short sell");
    });
  }
});

var AppView = Backbone.View.extend({
  el: $(document),
  initialize: function() {
    _.bindAll(this, "render");

    var i, portfolio_entries = [];

    if (AUTHENTICATED) {
      $(".trade-table input, .trade-table button").prop("disabled", true);
      $(".left-sidebar").scrollToFixed();

      // Transaction history
      if (TRANSACTIONS.length > 0) {
        var history = "";
        for (i = 0; i < TRANSACTIONS.length; ++i) {
          history += "<li>" +
            ((TRANSACTIONS[i][0] === 1) ? "Bought " : "Sold ") +
            TRANSACTIONS[i][4] +
            " of " +
            securityName(TRANSACTIONS[i][1], TRANSACTIONS[i][2], TRANSACTIONS[i][3]) +
            " for $" +
            TRANSACTIONS[i][5] +
            "</li>";
        }
        $("#history").html(history);
        $(".no_history").hide();
      } else {
        $(".yes_history").hide();
      }

      for (i = 0; i < PORTFOLIO.length; ++i) {
        portfolio_entries.push(new Entry({
          stock_id: PORTFOLIO[i][0],
          symbol: STOCKS[PORTFOLIO[i][0] - 1][0],
          liquid: PORTFOLIO[i][1],
          security: PORTFOLIO[i][2],
          security_name: securityName(PORTFOLIO[i][0], PORTFOLIO[i][2], PORTFOLIO[i][3]),
          strike: PORTFOLIO[i][3],
          shares: PORTFOLIO[i][4],
          value: PORTFOLIO[i][5],
          app: this.model
        }));
      }
    }

    var stock_entries = [];
    for (i = 0; i < STOCKS.length; ++i) {
      stock_entries.push(new Entry({
        stock_id: i + 1,
        symbol: STOCKS[i][0],
        liquid: STOCKS[i][1],
        sector: STOCKS[i][2],
        security: 0,
        security_name: securityName(i + 1, 0, -1),
        strike: -1,
        bid: STOCKS[i][3],
        ask: STOCKS[i][4],
        app: this.model
      }));
    }

    var option_entries = [];
    for (i = 0; i < OPTIONS.length; ++i) {
      option_entries.push(new Entry({
        stock_id: OPTIONS[i][0],
        symbol: STOCKS[OPTIONS[i][0] - 1][0],
        liquid: OPTIONS[i][1],
        security: OPTIONS[i][2],
        security_name: securityName(OPTIONS[i][0], OPTIONS[i][2], OPTIONS[i][3]),
        strike: OPTIONS[i][3],
        bid: OPTIONS[i][4],
        ask: OPTIONS[i][5],
        app: this.model
      }));
    }

    this.model.set({
      portfolio_table: new Table(portfolio_entries),
      stock_table: new Table(stock_entries),
      option_table: new Table(option_entries)
    });

    this.render();
  },
  render: function() {
    var i, entryView;

    // Render portfolio table
    if (AUTHENTICATED) {
      for (i = 0; i < this.model.get("portfolio_table").length; ++i) {
        entryView = new PortfolioEntryView({
          model: this.model.get("portfolio_table").models[i]
        });
        $(".portfolio-table").append(entryView.render().el);
      }
    }

    // Render stock table
    for (i = 0; i < this.model.get("stock_table").length; ++i) {
      entryView = new StockEntryView({
        model: this.model.get("stock_table").models[i]
      });
      $(".stock-table").append(entryView.render().el);
    }

    // Render option table
    for (i = 0; i < this.model.get("option_table").length; ++i) {
      entryView = new OptionEntryView({
        model: this.model.get("option_table").models[i]
      });
      $(".option-table").append(entryView.render().el);
    }

    if (AUTHENTICATED) {
      // Render transaction error graph
      var r = new Raphael("holder", 260, 120);
      var default_msg = "Cumulative error: " + CUMTERROR;
      $("#terror-info").html(default_msg);
      r.linechart(0, 0, 260, 120, TERRORS[0], TERRORS[2], {nostroke: false, axis: "0 0 0 0", symbol: "circle", smooth: true, shade: true}).hoverColumn(function() {
        $("#terror-info").html("Error on " + TERRORS[1][this.axis] + ": " + this.values[0]);
      }, function() {
        $("#terror-info").html(default_msg);
      }).symbols.attr({ r: 3 });
    }
  }
});

new AppView({model: new App()});

}());
