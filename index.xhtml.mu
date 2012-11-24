<?xml version="1.0" encoding="iso-8859-1"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta name="viewport" content="width=device-width; initial-scale=1.0; target-densitydpi=device-dpi; maximum-scale=1.0; minimum-scale=1.0; user-scalable=0;" />
    <meta name="viewport" content="width=device-width" />

    <title>magma</title>
    <link rel="Stylesheet" type="text/css" href="bundle.css?v={{cssChecksum}}" media="all"/>

{{#notPhone}}
    <style type="text/css" media="screen"
>
    /* <![CDATA[ */
    body > div {    

    }

    /* ]]> */
</style>
{{/notPhone}}
      
<style type="text/css" media="handheld">
/* <![CDATA[ */

/* ]]> */
</style>

  <style type="text/css">
  /* supervisor overrides */
  th.name { width: 1em !important }

  table.status { border: 1px solid gray; border-collapse: collapse; }
   </style>


  </head>
  <body>


    <div id="sections"> 

      <div class="section">

	<div class="pageStatus">Live updates: <span id="socketStatus">...</span>. Sensor display: <span id="sensorDisplayStatus">...</span></div>


	<p><a href="houseActivity" style="text-decoration: underline;">Activity feeds</a></p>
{{^notPhone}}
	<p><a href="#commands" style="text-decoration: underline; display: inline-block; padding: 30px">Skip to commands</a></p>
{{/notPhone}}
      </div>
	
      <div class="section">
	<div class="imgFrame"> <a href="/cam/livingRoom">living room<div style="background: url(imgCat/cam.jpg?salt={{salt}}) 0 -72px; width: 106px; height: 72px"/></a> </div>
	<div class="imgFrame"> <a href="/cam/sideYard">side yard    <div style="background: url(imgCat/cam.jpg?salt={{salt}}) 0 -144px; width: 106px; height: 72px"/></a> </div>
	<div class="imgFrame"> <a href="/cam/garage">garage         <div style="background: url(imgCat/cam.jpg?salt={{salt}}) 0 -216px; width: 106px; height: 72px"/></a> </div>
	<div class="imgFrame"> <a href="/cam/frontDoor">front door  <div style="background: url(imgCat/cam.jpg?salt={{salt}}) 0 -288px; width: 106px; height: 72px"/></a> </div>
	<div class="imgFrame"> <a href="/cam/ari">ari               <div style="background: url(imgCat/cam.jpg?salt={{salt}}) 0 0px; width: 106px; height: 72px"/></a> </div>
	<div style="clear:both;"/>
	<div > <a href="/cam/all">All cameras at once</a></div>
      </div>

      <div class="section">
	<form method="post" action="microblogUpdate">
	  <input type="text" name="msg" style="width:310px" autocomplete="off"/> <span id="blogChars"/> <input type="submit" value="Post to microblogs"/>
	    <!-- query the user to see what ublogs they have, so we could list them 
		 in advance -->
	</form>
      </div>

      <div class="section">
	<h2>Sensors</h2>
	<div class="sensor">Front door: <span id="dev-frontDoorMotion">?</span> <span id="dev-frontDoorOpen">?</span></div>
	<div class="sensor">Theater door: <span id="dev-theaterDoorOutsideMotion">?</span> <span id="dev-theaterDoorOpen">?</span></div>
	<div class="sensor">Bedroom: <span id="dev-bedroomMotion">?</span></div>
      </div>

      <div class="section">
	<h2>Temperatures</h2>
	{{> tempsection}}
      </div>

      <div class="section">
	<h2>Power meter</h2>
	Units don't seem to be in watts, yet.

	<div><a href="http://graphite.bigasterisk.com/render/?width=900&amp;height=583&amp;target=keepLastValue(system.house.powerMeter_w)&amp;from=-15hours&amp;yMin=0&amp;hideLegend=true"><div style="background: url(imgCat/power.png?salt={{salt}}) 0 0px; width: 240px; height: 150px"/></a></div>
	<div style="clear: both"/>

	<h2>Solar output (W)</h2>
	<div><a href="http://graphite.bigasterisk.com/render/?width=900&amp;height=583&amp;target=system.house.solar.power_w&amp;from=-15hours&amp;areaMode=all&amp;yMax=4000&amp;hideLegend=true">
	  <div style="background: url(imgCat/power.png?salt={{salt}}) 0 -150px; width: 240px; height: 150px"/>

	</a></div>

	<div class="prevSolar">
	  <div style="background: url(imgCat/power.png?salt={{salt}}) 0 -300px; width: 240px; height: 90px; opacity: .8"/>
	</div>
	<div class="prevSolar">
	  <div style="background: url(imgCat/power.png?salt={{salt}}) 0 -390px; width: 240px; height: 90px; opacity: .6"/>
	</div>
	<div class="prevSolar">
	  <div style="background: url(imgCat/power.png?salt={{salt}}) 0 -480px; width: 240px; height: 90px; opacity: .4"/>
	</div>

      </div>

      <div class="section">
	<div class="links music">
	  <h2><div class="icon music"/>Music</h2>
	  <div><a href="/music/dash/playlist">drew's desk</a></div>
	  <div>
	    <a href="/music/slash/playlist">living room</a> 	  
	    <form style="display:inline" method="post" action="http://10.1.0.21:9049/speak"><input type="input" name="say"/><input type="submit" value="Speak"/></form>
	  </div>
	  <div><a href="/music/bang/playlits">bedroom</a> </div>
	  <div><a href="/music/star/playlist">ari's room</a> </div>
	  <div><a href="http://10.1.0.1:9041/">gnump3d music server (internal net only)</a></div>
	</div>
      </div>

      <div class="section" id="frontDoor">
	<h2>Front door message</h2>
	<div><textarea rows="3" cols="21" data-bind='value: message, valueUpdate: "afterkeydown"'></textarea></div>
	<div><input type="text" data-bind="enable: lastLineEnable, value: lastLine"/></div>
	<div id="frontDoorSave"></div>
      </div>

      <div class="section">
	<h2><a href="/nagios/cgi-bin/status.cgi?host=all">Service monitor</a></h2>
	<div class="services">{{{nagios}}}</div>
      </div>

      <div class="section">
	<h2>USAA Transactions:</h2>
	{{{recentTransactions}}}
      </div>

      <div class="section">
	<h2>Wifi users</h2>
	{{{wifiTable}}}

	<div>Routers: <a href="/tomato1/status-devices.asp">bigasterisk3</a> <a href="/tomato2/status-devices.asp">bigasterisk4</a></div>

	<div><button id="recentExpand">&gt;</button>Recent visitors...</div>
	<div style="display:none">
	  <table id="recentVisitors">
	    <tbody>
	    </tbody>
	  </table>
	</div>
      </div>

      <div class="section">
	<h2>VPN users</h2>
<table class="vpn">
<tr>
<th></th>
<th>real</th>
<th>bytes</th>
<th>Connected for</th>
</tr>
	{{#vpnTable}}
	<tr>
<td><a href="http://{{virtAddress}}">{{commonName}}</a></td>
<td>{{realAddressIpOnly}}</td>
<td>&darr; {{bytesRecv}} &uarr; {{bytesSent}}</td>
<td>{{connForPretty}}</td>
</tr>
	{{/vpnTable}}
</table>
      </div>

{{#showMunin}}
    <div class="section">
      <div class="graph munin"><h1>bang mem</h1> <a href="/magma/munin/bang/bang/index.html"> <div style="background: url(imgCat/munin.jpg?salt={{salt}}) -13px -10px; height:154px"/> </a> </div>
      <div class="graph munin"><h1>cpu</h1>      <a href="/magma/munin/bang/bang/index.html"> <div style="background: url(imgCat/munin.jpg?salt={{salt}}) -13px -164px; height:154px"/> </a> </div> 
      <div style="clear:both"/>

      <div class="graph munin"><h1>slash mem</h1><a href="/magma/munin/slash/slash/index.html"> <div style="background: url(imgCat/munin.jpg?salt={{salt}}) -13px -317px; height:154px"/> </a> </div>
      <div class="graph munin"><h1>cpu</h1>      <a href="/magma/munin/slash/slash/index.html"> <div style="background: url(imgCat/munin.jpg?salt={{salt}}) -13px -479px; height:154px"/> </a> </div>
      <div style="clear:both"/>
    </div>
{{/showMunin}}

    <div class="section">
      <div class="graph" style="height: 150px">
	<h1>phone batteries</h1>
	<a href="http://graphite.bigasterisk.com/render/?width=800&amp;height=400&amp;target=keepLastValue(system.phone.drewepic.battery_pct)&amp;from=-56hours&amp;yMin=0&amp;yMax=100&amp;fontSize=12&amp;lineWidth=6"><img src="http://graphite.bigasterisk.com/render/?width=158&amp;height=125&amp;target=keepLastValue(system.phone.drewepic.battery_pct)&amp;from=-8hours&amp;yMin=0&amp;yMax=100&amp;fontSize=7&amp;lineWidth=3&amp;salt={{salt}}" width="158" height="125"/></a>
      </div>

      <div class="graph">
	<h1>inbox</h1>
	<img src="http://graphite.bigasterisk.com/render/?width=158&amp;height=75&amp;target=system.msg.inbox_messages.drewp&amp;from=-60days&amp;areaMode=all&amp;hideLegend=true&amp;fontSize=7&amp;yMin=0&amp;salt={{salt}}" width="158" height="75"/>
      </div>

      <div style="clear:both"/>

      <div class="graph">
	<h1>eon load</h1>
	<img src="http://graphite.bigasterisk.com/render/?width=158&amp;height=75&amp;target=system.host.eon.load&amp;from=-10hours&amp;areaMode=all&amp;hideLegend=true&amp;fontSize=7&amp;yMin=0&amp;salt={{salt}}" width="158" height="75"/>
      </div>

      <div class="graph" style="height: 150px">
	<h1>dsl activity</h1>
	<a href="http://graphite.bigasterisk.com/render/?width=800&amp;height=500&amp;target=system.net.bytesPerSec.in&amp;target=system.net.bytesPerSec.out&amp;from=-20minutes&amp;fontSize=11&amp;yMin=0&amp;yMax=300000"><img src="http://graphite.bigasterisk.com/render/?width=158&amp;height=125&amp;target=system.net.bytesPerSec.in&amp;target=system.net.bytesPerSec.out&amp;from=-10minutes&amp;fontSize=7&amp;yMin=0&amp;yMax=300000&amp;salt={{salt}}" width="158" height="125"/></a>
      </div>

      <div style="clear:both"/>
    </div>
    
    <div class="section">
      <a name="commands"/>
      <div class="commands">
	{{{commands}}}
      </div>
      <div><a href="dynCommands/">debug these</a></div>
    </div>

    <div class="section">
      <div><a href="services">Other services</a></div>

      <div>Supervisor: <a href="/supervisor/bang/">bang</a> 
      <a href="/supervisor/dash/">dash</a> 
      <a href="/supervisor/slash/">slash</a> 
      <a href="/supervisor/star/">star</a></div>

      <div><a href="/supervisor/bang/index.html?action=restart&amp;processname=ajaxterm_8022">restart ajaxterm</a></div>
    </div>
  </div>    
  
  {{{loginBar}}}

   <script type="text/javascript"> var notPhone=false; var initialSensorDisplay={{{initialSensorDisplay}}};</script>
{{#notPhone}}
   <script type="text/javascript"> notPhone=true; </script>
{{/notPhone}}

    <script type="text/javascript" src="bundle.js?v={{bundleChecksum}}"></script>
  </body>
</html>