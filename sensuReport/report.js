$(function () {
    /*
    see https://github.com/sensu/sensu/wiki/Sensu%20API
    */  

    var raf = Modernizr.prefixed('requestAnimationFrame', window);
    function animLoop(cb, interval) { 
	// like setInterval but with an immediate call and *no calls* when you're on a different tab
	function loop() {
	    cb();
	    setTimeout(function () { raf(loop); }, interval);
	}
	loop();
    }

    function durationFormat(secs) {
	// silly moment.js forces anything under 45 sec to be just 'seconds ago'
	secs = Math.round(secs);
	if (secs < 45) {
	    return secs + (secs == 1 ? " second" : " seconds");
	}
	return moment.duration(secs, 'seconds').humanize();
    }

    function updateEvents(currentEvents) {
	$.getJSON("../events", function (events) {
	    var eventsToClear = {};
	    _.each(_.pairs(currentEvents), function (p) { 
		if (p[1] !== null) { 
		    eventsToClear[p[0]] = true;
		}
	    });
	    events.forEach(function (ev) {
		var clientCheckName = ev.client + "." + ev.check;
		var eventObservable = currentEvents[clientCheckName];
		if (!eventObservable) {
		    return; // I think this is no longer a current, subscribed check
		}
		eventObservable(ev);
		delete eventsToClear[clientCheckName];
	    });
	    _.keys(eventsToClear).forEach(function (ccn) {
		currentEvents[ccn](null);
	    });
	});
    }

    function updateLastIssue(lastIssue) {
	$.getJSON("../aggregates", function (aggregates) { 
	    aggregates.forEach(function (agg) {
		var latest = _.max(agg.issued) * 1000;
		if (!_.has(lastIssue, agg.check)) {
		    lastIssue[agg.check] = ko.observable(latest);
		} else {
		    lastIssue[agg.check](latest);
		}
	    });
	});
    }

    function requestCheckNow(check) {
	$.ajax({
	    url: "../check/request",
	    type: "POST",
	    data: JSON.stringify({check: check.name, subscribers: check.subscribers})
	});
    }

    function getChecksAndClients(clientChecks, lastIssue) {
	/*
	adds rows to clientChecks; makes observables in lastIssue as needed
	*/	
	async.parallel({
	    clients: function (cb) { return $.getJSON("../clients", function (data) { cb(null, data) }); },
	    checks: function (cb) { return $.getJSON("../checks", function (data) { cb(null, data) }); },
	}, function (err, results) {
	    results.clients.forEach(function (client) {
		client.shortName = client.name.replace(/\..*/, "");
	    });

	    _.sortBy(results.checks, 'name').forEach(function (check) {
		if (!_.has(lastIssue, check.name)) {
		    lastIssue[check.name] = ko.observable(null);
		}
		check.lastIssue = lastIssue[check.name];

		_.sortBy(results.clients, 'name').forEach(function (client) {
		    if (_.intersection(client.subscriptions, check.subscribers).length > 0) {
			var clientCheckName = client.name + "." + check.name;
			currentEvents[clientCheckName] = ko.observable(null);

			clientChecks.push($.extend({
			    client: client, 
			    currentEvent: currentEvents[clientCheckName],
			    request: function () { requestCheckNow(check); },
			}, check));
		    }
		});
	    });
	});
    }

    var model = {
	showSuccessRows: ko.observable(true),
	clientChecks: ko.observableArray([]),
	now: ko.observable(+new Date()),
	durationFormat: durationFormat,
	displayInterval: function (check) {
	    return durationFormat(check.interval);
	},
    };

    var lastIssue = {}; // check name : observable(ms_of_last_issue)
    var currentEvents = {}; // clientname.checkname : observable with event

    getChecksAndClients(model.clientChecks, lastIssue);

    animLoop(function () { updateEvents(currentEvents); }, 5000);
    animLoop(function () { updateLastIssue(lastIssue); }, 5000);
    animLoop(function () { model.now(+new Date()); }, 1000);

    ko.applyBindings(model);
});