$(function () {
    $("#recentExpand").click(function () { 
	$(this).text("V");
	$(this).parent().next().show();
	$("#recentVisitors").load("/activity/f/netVisitors.xhtml?order=desc", function () { setTimeout(function () { $(window).trigger("relayout"); }, 500); });
    });

    $("input[name=msg]").keyup(function () {
	var chars = $("form[action=microblogUpdate] input[type=text]").val().length;
	$("#blogChars").text("("+chars+")");
    });

    function TempGraph() {
	var self=this;
	var graphImg = $(".graphLayout img");
	self.hours = 26;
	this.setImgSrc = function() {
	    graphImg.attr(
		"src", "http://graphite.bigasterisk.com/render/?"+
		    $.param({
			width: "400", height: "250",
			target: ["system.house.temp.downstairs",
				 "system.house.temp.ariroom",
				 "keepLastValue(system.house.temp.bedroom)",
				 "system.house.temp.livingRoom",
				 "system.noaa.ksql.temp_f",
				 "system.house.temp.frontDoor"],
			from: "-"+self.hours+"hours",
			hideAxes: "false",
			hideLegend: "true",
			lineWidth: "1.5",
			yMin: "40", yMax: "90",
		    }, true));
	}

	self.setImgSrc();
	$("input[name=tempHours]").click(function () {
	    self.hours = $("input[name=tempHours]:checked").attr("value");
	    self.setImgSrc();
	});
	$("#th3")[0].checked = true;
    }
    var t=new TempGraph();

    $("form[method=post][action=addCommand]").submit(function () {
	var resp = $("<div>").addClass("response");
	$(this).append(resp);
	resp.text("Sending...");
	$.ajax({
	    type: "POST",
	    url: $(this).attr("action"), 
	    data: $(this).serialize(), 
	    success: function (result) {
		resp.addClass("success");
		resp.text(result);
		setTimeout(function () { resp.fadeOut(1000, function () { resp.remove(); }) }, 2000);
	    },
	    error: function (jqXHR, textStatus, errorThrown) {
		resp.addClass("error");
		resp.text(textStatus);
	    }
	});
	return false;
    });

    function FrontDoor() {
	var self = this;

// goal is to make this much shorter and especially to stop the ringing effect where i get my own updates after a big delay. if i have sent an update that's later than the incoming one, ignore that incoming one (and wait for the echo of my own one). can we do this with version counters to avoid dealing with clock skew? i say i'm editing 15 to make 15.1, and if i receive 14 i can ignore it. Or just delay my updates?
	this.message = ko.observable("...");
/*
	    read: function () {
		$.get("frontDoor/message", function (data){ 
		    self.message(data);
//not going great. switch to normal obs
		});
		return _message;
	    },
	    write: function (v) {
		_message = v;
		console.log("wr", v);
	    }
	}),
*/
	this.lastLine =  ko.observable("...");
	this.lastLineEnable = ko.observable(false);
    };

    var frontDoor = new FrontDoor
    ko.applyBindings(frontDoor, document.getElementById("frontDoor"));

    var loading = false;

    var pendingUpdate = null;

    function frontDoorUpdate() {
	$("#frontDoorSave").text("sync");
	$.get("frontDoor/message", function (data){ 
	    loading = true;
	    frontDoor.message(data);
	    $("#frontDoorSave").text("");
	    loading = false;
	});

	$.get("frontDoor/lastLine", function (data){
	    frontDoor.lastLine(data) 
	});
    }
    frontDoorUpdate();
    frontDoor.message.subscribe(function (msg) {
	if (loading) {
	    return;
	}
	$("#frontDoorSave").text("save");
	// this put is echoing back as a change event, which makes
	// another socketio request and sends me fetching the new
	// value (which is probably what I just typed)
	$.ajax({
	    type: "PUT",
	    url: "frontDoor/message", 
	    data: msg, 
	    success: function () {
		$("#frontDoorSave").text("");
	    }
	});
    });

    
    function isotopeSections() {
	var iso = $('#sections').isotope({
	    itemSelector : '.section',
	    layoutMode : 'masonry'
	});
	$(window).bind("relayout", function () { iso.isotope("reLayout"); });
    }	
    $(".col2").isotope({
	itemSelector: "div",
	layoutMode: 'fitRows',
    });

    if (notPhone) {
	setTimeout(isotopeSections, 50);
    }

    var socket = io.connect('/magma/', {resource: "magma/socket.io"});

    var disconnected = $("#disconnected");

    ["reconnect_failed", "error", "disconnect", "connect_failed"
    ].forEach(function (disconnectEvent) {
	socket.on(disconnectEvent, function (r) { 
	    disconnected.show(); 
	    $(window).trigger("relayout"); 
	});
    });
    socket.on("connecting", function (how) { 
	disconnected.hide(); 
	$(window).trigger("relayout"); 
    });

    socket.of("").on("frontDoorChange", function (r) {
	clearTimeout(pendingUpdate);
	pendingUpdate = setTimeout(frontDoorUpdate, 1200);
	$("#frontDoorSave").text("sync");
    });

    function updateSensors(display) {
	display.forEach(function (row) {
	    $("#"+row.id).attr("class", row.cssClass).text(row.value);
	});
    }
    updateSensors(initialSensorDisplay);
    socket.of("").on("sensorChange", updateSensors);

});