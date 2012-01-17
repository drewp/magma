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
    socket.join("updates");

    setTimeout(function () { io.sockets.in("updates").emit("hey", "data") }, 1000);
});

function httpGet(url, headers, cb) {
    var shred = new Shred;
    shred.get({
	url: url,
	headers: headers,
	on: {
	    200: function (response) {
		cb(response.content.body);
	    },
	    response: function (response) {
		inspect(response);
		cb("error: "+response);
	    }
	}
    });
}

app.get("/", function (req, res) {
    res.header("content-type", "application/xhtml+xml");
    httpGet("http://bang:9023/_loginBar", {"Cookie": req.header("cookie")}, function (loginBar) {
    httpGet("http://bang:9094/", {}, function (recentTransactions) {
    httpGet("http://bang:9070/table", {}, function (wifiTable) {
    httpGet("http://bang:8006/commands", {"x-foaf-agent" : req.header("x-foaf-agent")}, function (commands) {
    httpGet("http://bang:8006/tempSection", {"x-foaf-agent" : req.header("x-foaf-agent")}, function (tempSection) {
    httpGet("http://bang:8012/", {}, function (nagios) {
	wifiTable = wifiTable.replace(/^[\s\S]*?<div/, "<div");

	var ctx = {
	    notPhone: !req.header("user-agent").match(/webOS|iPhone/),
	    loginBar: loginBar,
	    wifiTable: wifiTable,
	    commands: commands,
	    nagios: nagios,
	    recentTransactions: recentTransactions,
	    salt: +new Date,
	    showMunin: true,
	    temps: JSON.parse(tempSection),
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
    });
    });
    });
    });
});    
