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

Mu.templateRoot = '.';
var proxy = new httpProxy.RoutingProxy();

app.listen(8010);
app.use(express.bodyParser()); // allows req.body.someParam
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
		callback(null, file.replace(/\+\+new Date/mig, 
					    '\+\(\+new Date)'));
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
	//timeout: {seconds: 2},
	on: {
	    200: function (response) {
		console.log(url, "in", +new Date() - t1);
		cb(null, response.content.body);
	    },
	    response: function (response) {
		inspect(response);
		cb(null, "error: "+response);
	    }
	}
    });
}

var staticDir = express.static(__dirname + '/static/');
app.get("/icons", function (req, res) {
    req.url = "icons-nq8.png";
    return staticDir(req, res); 
});

["/services", "/addCommand", "/microblogUpdate", "/garage/*", "/houseActivity"
].forEach(function (url) {
    var dest = {host: 'localhost', port: 8006};
    app.get(url, function (req, res) { proxy.proxyRequest(req, res, dest); });
    app.post(url, function (req, res) { proxy.proxyRequest(req, res, dest); });
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
	    nagios: async.apply(httpGet, "http://bang:8012/", hh)
	}, 
	function (err, r) {
	    if (err) {
		throw err;
	    }
	    
	    r.wifiTable = r.wifiTable.replace(/^[\s\S]*?<div/, "<div");

	    var ctx = {
		notPhone: !req.header("user-agent").match(/webOS|iPhone/),
		loginBar: r.loginBar,
		wifiTable: r.wifiTable,
		commands: r.commands,
		nagios: r.nagios,
		recentTransactions: r.recentTransactions,
		salt: +new Date,
		showMunin: true,
		temps: JSON.parse(r.tempSection),
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
    res.send("");
});

