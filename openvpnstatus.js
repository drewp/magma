var net = require('net');

exports.getOpenvpnClients = function (cb) {
    // oops- this should go through rdf to get into the graph

    function parse(buffer) {
	var out = [];
	buffer.split("\n").forEach(function (line) {
	    if (line.match(/^CLIENT_LIST/)) {
		var f = line.split("\t");
		var connForSec = (new Date() - new Date(parseInt(f[7])*1000)) / 1000;
		var rec = {
		    commonName: f[1], 
		    realAddress: f[2], 
		    realAddressIpOnly: f[2].split(/:/)[0],
		    virtAddress: f[3], 
		    bytesRecv: f[4], 
		    bytesSent: f[5], 
		    connFor: connForSec,
		    connForPretty: (
			(connForSec > 3600) ? 
			    (Math.round(connForSec / 3600) + " hours") : 
			    (Math.round(connForSec / 60) + " mins"))
		};
		out.push(rec);
	    }
	});
	return out;
    }

    var buffer = "";
    var conn = net.createConnection(2005, 'localhost', function () {
	conn.write("status 3\n");
    });
    conn.addListener("data", function (data) {
	buffer += data;
	if (buffer.indexOf("\nEND") != -1) {
	    conn.end();
	    var out = parse(buffer);
	    cb(false, out);
	}
    });
}

