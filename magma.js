#!buildout_bin/node

var debug=true;
var inspect = require('eyes').inspector({styles: {all: 'magenta'}, 
					 maxLength: 20000});
var Shred = require('shred');
var soupselect = require('soupselect');
var htmlparser = require('htmlparser');
var fs     = require('fs');
var Connect = require('connect');
var assetManager = require('connect-assetmanager');
var assetHandler = require('connect-assetmanager-handlers');
var express = require('express'),
    app = express.createServer(),
    io = require('socket.io').listen(app);
var Mu = require('Mu');
var async = require('async');
var httpProxy = require('http-proxy');
var rdf = require('./rdf.js');

Mu.templateRoot = '.';
var proxy = new httpProxy.RoutingProxy();

app.listen(8010);

//app.use(express.static(__dirname+"/static", {maxAge: 86400*10*1000})); // may never be used if i get everything into assetManager
if (debug) app.use(Connect.logger());
//app.use(Connect.conditionalGet());
//app.use(Connect.cache());
//app.use(Connect.gzip());
var am = assetManager({
    'js' : {
	path: __dirname + "/",
	route: /\/bundle\.js/,
	dataType: 'js',
	files: ["static/jquery-1.7.1.js", 
		"static/jquery.isotope-1.5.07.js", // 5k min+gzip
		debug ? "static/knockout-2.0.0.debug.js" : "static/knockout-2.0.0.js",
		'parts/node/lib/node_modules/socket.io/node_modules/socket.io-client/dist/socket.io.js',
		"tomato_config.js",
		"magma_gui.js"
	       ],
	debug: debug,
	// also in map3.js
	postManipulate: [
	    function (file, path, index, isLast, callback) {
		// minifier bug lets '++new Date' from
		// socket.io.js into the result, which is a parse error.
		callback(null, file
			 .replace(/\+\+new Date/mig, '\+\(\+new Date)')
			 // in knockout
			 .replace(/\+\+\+([a-z]+)/g, '\+(\+\+$1)'));
	    }
	]
    },
    'css' : {
	path: __dirname + "/",
	route: /\/bundle\.css/,
	dataType: 'css',
	debug: debug,
	files: ["static/nagios/status.css", "magma_gui.css"]
    }
});
app.use(am);


console.log('serving on http://localhost:8010/');

io.configure(function () {
    io.set('transports', ['xhr-polling']);
    io.set('log level', 2);

    // really I want the socket.io.js file to be in the assetManager bundle
    if (!debug) {
	io.enable('browser client minification');
	io.enable('browser client gzip');
	io.enable('browser client etag');      
    }
});

io.sockets.on('connection', function (socket) {
    console.log("connect", socket.id)
    socket.on('disconnect', function (reason) {
	console.log("disconnect", socket.id);
    });
});

function httpGet(url, headers, cb) {
    /* cb is called with (error, result) but i didn't implement errors yet */
    var shred = new Shred;
    var t1 = +new Date();
    shred.get({
	url: url,
	headers: headers,
	timeout: {seconds: 2}, // no effect :( :(
	on: {
	    200: function (response) {
		console.log(url, "in", +new Date() - t1);
		cb(null, response.getHeader('Content-Type') == "application/json" ? response.content.data : response.content.body);
	    },
	    response: function (response) {
		console.log("error", url, response);
		cb(null, "error from "+url);
	    }
	}
    });
}

var staticDir = express.static(__dirname + '/static/');
app.get("/icons", function (req, res) {
    req.url = "icons-nq8.png";
    return staticDir(req, res); 
});
app.get("/static/json-template.js", function (req, res) {
    req.url = "json-template.js";
    return staticDir(req, res);
});

["/services", "/addCommand", "/microblogUpdate", "/garage/*", "/houseActivity"
].forEach(function (url) {
    var dest = {host: 'localhost', port: 8006};
    app.all(url, function (req, res) { proxy.proxyRequest(req, res, dest); });
});

app.get("/", function (req, res) {
    res.header("content-type", "application/xhtml+xml");

    var ch = {"Cookie": req.header("cookie")};
    var hh = {"x-foaf-agent" : req.header("x-foaf-agent")};
    async.parallel(
	{
	    loginBar: async.apply(httpGet, "http://bang:9023/_loginBar", ch),
	    recentTransactions: async.apply(httpGet, "http://bang:9094/", hh),
	    wifiTable: async.apply(httpGet, "http://bang:9070/table", hh),
	    commands: async.apply(httpGet, "http://bang:8006/commands", hh),
	    tempSection: async.apply(httpGet,"http://bang:8006/tempSection",hh),
	    nagios: async.apply(httpGet, "http://bang:8012/", hh),
	    sensorGraphs: async.apply(httpGet, "http://bang:9071/ntGraphs", hh),
	}, 
	function (err, r) {
	    console.log("async done")
	    if (err) {
		throw err;
	    }
	    
	    r.wifiTable = r.wifiTable.replace(/^[\s\S]*?<div/, "<div");

	    var ctx = {
		notPhone: !req.header("user-agent").match(/webOS|iPhone|Mobile/),
		loginBar: r.loginBar,
		wifiTable: r.wifiTable,
		commands: r.commands,
		nagios: r.nagios,
		recentTransactions: r.recentTransactions,
		salt: +new Date,
		showMunin: true,
		temps: JSON.parse(r.tempSection),
		sensorDisplay: JSON.stringify(displayForSensorGraphs(r.sensorGraphs)),
		bundleChecksum: am.cacheHashes['js'],
		cssChecksum: am.cacheHashes['css']
	    };
	    Mu.render('./index.xhtml', ctx, {cached: !debug}, 
		      function (err, output) {
			  if (err) {
			      throw err;
			  }
			  output.addListener('data', 
					     function (c) { res.write(c); })
			      .addListener('end', function () { res.end(); });
		      });
	});
});    


var internal = express.createServer();
internal.listen(8014);
internal.use(express.bodyParser());
console.log('internal connections to http://localhost:8014/');

internal.post("/frontDoorChange", function (req, res) {
    io.sockets.emit("frontDoorChange", req.body);
    res.send("ok");
});

rdf.prefixes.addAll({
    foaf: "http://xmlns.com/foaf/0.1/",
    bigast: "http://bigasterisk.com/",
    room: "http://projects.bigasterisk.com/room/",
    dev: "http://projects.bigasterisk.com/device/",
    env: "http://projects.bigasterisk.com/device/environment"
});

function displayForSensorGraphs(graphs) {
    var g = rdf.createGraph();
    rdf.parseNT(graphs.input, null, null, null, g)
    rdf.parseNT(graphs.inferred, null, null, null, g)

    var display = [];

    [{subject: "dev:frontDoorMotion", normal: "room:noMotion", 
      normalLabel: "no motion", activeLabel: "motion"},
     {subject: "dev:frontDoorOpen", normal: "room:closed", 
      normalLabel: "closed", activeLabel: "open"},
     {subject: "dev:theaterDoorOutsideMotion", normal: "room:noMotion", 
      normalLabel: "no motion", activeLabel: "motion"},
     {subject: "dev:theaterDoorOpen", normal: "room:closed", 
      normalLabel: "closed", activeLabel: "open"},
     {subject: "dev:bedroomMotion", normal: "room:noMotion", 
      normalLabel: "no motion", activeLabel: "motion"},
    ].forEach(function (row) {
	g.match(rdf.iri(row.subject)).forEach(function (t, g) {
	    var isNormal = t.object.equals(rdf.iri(row.normal));
	    display.push({
		id: row.subject.replace(":", "-"), 
		cssClass: isNormal ? "normal" : "active",
		value: isNormal ? row.normalLabel : row.activeLabel
	    });
	});
    });
    return display;
}

internal.post("/reasoningChange", function (req, res) {
    var display = displayForSensorGraphs(req.body);
    io.sockets.emit("sensorChange", display);
    res.send("ok");
});