var server = require('http').createServer(function(req, response){
    response.write("nowserver");
    response.end();
});
var everyone = require("now").initialize(server, {resource: "foo"});
server.listen(9081);

var currentMain;
var currentBot="bot1";
console.log("start", currentBot);
function updateEveryone() {
   everyone.now.updateMsg(currentMain, currentBot);
}

everyone.connected(function(){
	//    updateEveryone();
    console.log("conn", this.now);
});

everyone.now.editedMain = function (m) {
    console.log("edited", m);
    currentMain = m;
    updateEveryone();
    // also post it to host.py for the LCD, and repeat this periodically
}


// in here, compose the bottom line with time and temp. push it to
// listeners and to the LCD