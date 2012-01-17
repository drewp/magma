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

/*
nowjs not working yet
    now.updateMsg = function (main, bot) {
	$("#frontDoorLcd").val(main);
	$("#frontDoorBottomLine").val(bot);
	// restore cursor position if they were editing?
    }
    $("#frontDoorLcd").keyup(function () { now.editedMain($(this).val()); });
*/

/*
    (function () {
// needs to route to frontdoormsg instead, who could probably render this whole widget
	$.get("frontDoor/lcd/lastLine", function (data){ $("#frontDoorLastLine").val(data) });
	var fd = $("#frontDoorLcd")
	$.get("frontDoor/lcd", function (data){ fd.val(data) });
	
	fd.keyup(function() {
	    $("#frontDoorSave").css("color", "yellow");
	    $.post("frontDoor/lcd", {message: fd.val()}, function () {
		$("#frontDoorSave").css("color", "black");
	    });
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
    socket.emit('join', 'hey');
    socket.on('hey', function (r) { console.log("update", r) });


});