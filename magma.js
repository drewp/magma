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

Mu.templateRoot = '.';

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
		"static/jquery.isotope-1.5.07.js",
		"tomato_config.js",
		"magma_gui.js"
	       ],
	debug: debug,
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
    socket.emit("ping","3");
    socket.join("updates");

    setTimeout(function () {
	console.log("pinging"); 
	socket.emit("ping", "2");
	io.sockets.in("updates").emit("ping", "1");
 }, 1000);
});

function httpGet(url, headers, cb) {
    /* cb is called with (error, result) but i didn't implement errors yet */
    var shred = new Shred;
    var t1 = +new Date();
    shred.get({
	url: url,
	headers: headers,
	on: {
	    200: function (response) {
		//console.log(url, "in", +new Date() - t1);
		cb(null, response.content.body);
	    },
	    response: function (response) {
		inspect(response);
		cb(null, "error: "+response);
	    }
	}
    });
}

app.get("/", function (req, res) {
    res.header("content-type", "application/xhtml+xml");

    var hh = {"x-foaf-agent" : req.header("x-foaf-agent")};
    async.parallel(
	{
	    loginBar: async.apply(httpGet, "http://bang:9023/_loginBar", {"Cookie": req.header("cookie")}),
	    recentTransactions: async.apply(httpGet, "http://bang:9094/", hh),
	    wifiTable: async.apply(httpGet, "http://bang:9070/table", hh),
	    commands: async.apply(httpGet, "http://bang:8006/commands", hh),
	    tempSection: async.apply(httpGet, "http://bang:8006/tempSection", hh),
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
