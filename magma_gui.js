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
			width: "240", height: "250",
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

    function frontDoorUpdate() {
	$.get("frontDoor/message", function (data){ 
	    loading = true;
	    frontDoor.message(data);
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
	$("#frontDoorSave").css("color", "yellow");
	// this put is echoing back as a change event, which makes
	// another socketio request and sends me fetching the new
	// value (which is probably what I just typed)
	$.ajax({
	    type: "PUT",
	    url: "frontDoor/message", 
	    data: msg, 
	    success: function () {
		$("#frontDoorSave").css("color", "black");
	    }
	});
    });

    
    //$.get("frontDoor/lastLine", function (data){ frontDoor.lastLine(data) });

	
/*
	fd.keyup(function() {
	});
    })();
*/

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
    socket.on('reconnect_failed', function (r) { disconnected.show(); });
    socket.on("error",            function (r) { disconnected.show(); });
    socket.on("disconnect",       function () { disconnected.show(); });
    socket.on("connect_failed",   function (r) { disconnected.show(); })
    socket.on("connecting",       function (how) { disconnected.hide(); });

    socket.of("").on("frontDoorChange", function (r) {
	frontDoorUpdate();
    });

});