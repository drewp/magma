#!buildout_bin/node

var debug=true;
var inspect = require('eyes').inspector({styles: {all: 'magenta'}, 
					 maxLength: 20000});
var request = require('request');
var soupselect = require('soupselect');
var htmlparser = require('htmlparser');
var fs     = require('fs');
var Connect = require('connect');
var assetManager = require('connect-assetmanager');
var assetHandler = require('connect-assetmanager-handlers');
var express = require('express'),
    app = express(),
    http = require('http'),
    server = http.createServer(app),
    io = require('socket.io').listen(server);
var Mu = require('Mu');
var async = require('async');
var httpProxy = require('http-proxy');
var rdf = require('./rdf.js');
var log = require('tracer').colorConsole();
var getOpenvpnClients = require("./openvpnstatus.js").getOpenvpnClients;
Mu.templateRoot = '.';
var proxy = new httpProxy.RoutingProxy();

server.listen(8010);

//app.use(express.static(__dirname+"/static", {maxAge: 86400*10*1000})); // may never be used if i get everything into assetManager
if (debug) app.use(Connect.logger());
//app.use(Connect.conditionalGet());
//app.use(Connect.cache());
//app.use(Connect.gzip());

// chrome audit says 
// The following publicly cacheable resources contain a Set-Cookie header. This security vulnerability can cause cookies to be shared by multiple users.
var am = assetManager({
    'js' : {
	path: __dirname + "/",
	route: /\/bundle\.js/,
	dataType: 'js',
	files: ["static/jquery-1.7.1.js", 
		"static/jquery.isotope-1.5.23.js", // 5k min+gzip
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
	files: ["magma_gui.css"]
    }
});
app.use(am);


log.info('serving on http://localhost:8010/');

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
    log.info("connect", socket.id)
    socket.on('disconnect', function (reason) {
	log.info("disconnect", socket.id);
    });
});

function httpGet(url, headers, cb) {
    /* cb is called with (error, result) but i didn't implement errors yet */

    var t1 = +new Date();
    request.get({
	url: url,
	headers: headers,
	timeout: 1000,

    }, function (error, response, body) {
	log.info(url, "returned in", +new Date() - t1, error);
	cb(error, body);
	// old shred one: cb(null, response.getHeader('Content-Type') == "application/json" ? response.content.data : response.content.body);
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
app.get("/static/garage-bundle.js", function (req, res) {
    // set cache forever..
    res.write(fs.readFileSync("static/jquery-1.9.1.min.js"));
    res.write(fs.readFileSync("static/jquery-ui-1.10.1.custom/js/jquery-ui-1.10.1.custom.min.js"));
    res.write(fs.readFileSync("static/jquery.ui.touch-punch.min.js"));
    res.end();
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
    log.info("root request start", ch, hh);

    var parts = {
	loginBar: {
	    url: "http://bang:9023/_loginBar", 
	    headers: ch
	},
	recentTransactions: {
	    url: "http://bang:9094/", 
	    headers: hh
	}, 
  	wifiTable: {
	    url: "http://bang:9070/table", 
	    headers: hh, 
	    convert: function (resp) { return resp.replace(/^[\s\S]*?<div/, "<div"); }
	},
	commands: { 
	    url: "http://bang:8007/commands/table", 
	    headers: hh
	},
	temps: {
	    url: "http://bang:8006/tempSection",
	    headers: hh, 
	    convert: function (resp) { return JSON.parse(resp); },
	    failed: {}
	},
	sensu: {
	    url: "http://bang:9101/table", 
	    headers: hh
	},
	initialSensorDisplay: {
	    url: "http://bang:9071/ntGraphs", 
	    headers: hh,
	    convert: function (resp) { return JSON.stringify(displayForSensorGraphs(JSON.parse(resp))); },
	    failed: "{}",
	},
	trails: {
	    url: "http://bang:9099/graph",
	    headers: hh,
	    convert: function (resp) {
		
		var mapLines = [];

		function ntFromTrig(trig) {
		    // (for very simple trig)
		    var i1 = trig.indexOf("\n"), i2 = trig.lastIndexOf("\n");
		    return trig.substr(i1 + 1, i2 - i1 - 2);
		}
		var g = rdf.createGraph();
		rdf.parseNT(ntFromTrig(resp), null, null, null, g);

		[rdf.iri("http://bigasterisk.com/foaf.rdf#drewp"),
		 rdf.iri("http://bigasterisk.com/kelsi/foaf.rdf#kelsi")].forEach(
		     function (user) {
			 g.match(user, rdf.iri("map:lastSeenAgo")).forEach(function (t) {
			     g.match(user, rdf.iri("map:lastDesc")).forEach(function (t2) {
                               var phrase1 = "";
                               g.match(user, rdf.iri("map:distanceToHomeM")).forEach(function (metersFromHome) {

                                 var milesFromHome = parseFloat(metersFromHome.object.toString()) * 0.000621371;
                                 phrase1 = " " + Math.round(milesFromHome) + "mi from home";
});
                                 var userLabel = user.toString().substr(
				     user.toString().indexOf("#"));
                                 mapLines.push({line: 
						userLabel + 
                                                phrase1 + ", last seen " + 
						t.object.toString() + " ago " + 
						t2.object.toString()});
                                
			     });
			 });
		     });
		return mapLines;
	    }
	}
    };
    var calls = {
	vpnTable: getOpenvpnClients
    };
    Object.keys(parts).forEach(function (k) {
	// debug // if (k != "commands") {return;}
	calls[k] = async.apply(httpGet, parts[k].url, parts[k].headers);
    });

    async.series(
	calls,
	function (err, r) {
	    log.info("async done", err)
	    
	    var ctx = {
		notPhone: !req.header("user-agent").match(/webOS|iPhone|Mobile/),
		salt: +new Date,
		showMunin: true,
		bundleChecksum: am.cacheHashes['js'],
		cssChecksum: am.cacheHashes['css']
	    };

	    Object.keys(parts).forEach(function (k) {
		if (r[k] === undefined) {
		    ctx[k] = parts[k].failed || (k + " failed");
		} else {
		    if (parts[k].convert) {
			r[k] = parts[k].convert(r[k]);
		    }
		    ctx[k] = r[k];
		}
	    });
	    if (r['vpnTable'] !== undefined) {
		ctx['vpnTable'] = r['vpnTable'];
	    } else { 
		ctx['vpnTable'] = 'failed';
	    }

	    Mu.render('./index.xhtml', ctx, {cached: !debug}, 
		      function (err, output) {
			  if (err) {
			      throw err;
			  }
			  output.addListener('data', 
					     function (c) { res.write(c); })
			      .addListener('end', function () { 
				  res.end(); 
				  log.info("root request finish");
			      });
		      });
	});
});    


var internal = express();
internal.listen(8014);
internal.use(express.bodyParser());
log.info('internal connections to http://localhost:8014/');

internal.post("/frontDoorChange", function (req, res) {
    io.sockets.emit("frontDoorChange", req.body);
    res.send("ok");
});

rdf.prefixes.addAll({
    foaf: "http://xmlns.com/foaf/0.1/",
    bigast: "http://bigasterisk.com/",
    room: "http://projects.bigasterisk.com/room/",
    dev: "http://projects.bigasterisk.com/device/",
    env: "http://projects.bigasterisk.com/device/environment",
    map: "http://bigasterisk.com/map#",
    host: "http://bigasterisk.com/host/"
});

function displayForSensorGraphs(graphs) {
    var g = rdf.createGraph();
    rdf.parseNT(graphs.input, null, null, null, g);
    rdf.parseNT(graphs.inferred, null, null, null, g);

    var display = [];

    function mon(host) {
      return {subject: "host:"+host+"/monitor", 
              predicate: "room:powerStateMeasured",
              normal: "room:off", 
              normalLabel: "monitor off", 
              activeLabel: "monitor on"
             };
    }
    
    [{subject: "dev:frontDoorMotion", predicate:"room:state", 
      normal: "room:noMotion", normalLabel: "no motion", activeLabel: "motion"},
     {subject: "dev:frontDoorOpen", predicate: "room:state", 
      normal: "room:closed", normalLabel: "closed", activeLabel: "open"},
     {subject: "dev:theaterDoorOutsideMotion", predicate: "room:state", 
      normal: "room:noMotion", normalLabel: "no motion", activeLabel: "motion"},
     {subject: "dev:theaterDoorOpen", predicate: "room:state", 
      normal: "room:closed", normalLabel: "closed", activeLabel: "open"},
     {subject: "dev:bedroomMotion", predicate: "room:state",
      normal: "room:noMotion", normalLabel: "no motion", activeLabel: "motion"},
     {subject: "dev:heater", predicate: "room:state", 
      normal: "room:off", normalLabel: "off", activeLabel: "on"},
     mon("bang"), mon("slash"), mon("dash"), mon("star")
    ].forEach(function (row) {
	g.match(rdf.iri(row.subject), rdf.iri(row.predicate)).forEach(
            function (t, g) {
	        var isNormal = t.object.equals(rdf.iri(row.normal));
	        display.push({
		    id: row.subject.replace(":", "-").replace("/", "-"), 
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
