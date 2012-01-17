<div xmlns="http://www.w3.org/1999/xhtml" class="graphLayout">
  <a href="http://graphite.bigasterisk.com/render/?width=720&amp;height=500&amp;target=system.house.temp.downstairs&amp;target=system.house.temp.ariroom&amp;target=keepLastValue(system.house.temp.bedroom)&amp;target=system.house.temp.livingRoom&amp;target=system.noaa.ksql.temp_f&amp;target=system.house.temp.frontDoor&amp;from=-100hours&amp;hideAxes=false&amp;hideLegend=false&amp;lineWidth=1.5&amp;yMin=35&amp;yMax=90">
    <img src="" width="240" height="250"/>
  </a>
  <div class="graphSidebar">
    {{#temps}}
    <div class="lineLegend temp-{{name}}">
      <span>&#8213;</span> {{name}} <div class="currentTemp">{{{val}}} </div>
    </div>
    {{/temps}}
  </div>
  <div class="graphUnder">
    <div><input type="radio" name="tempHours" value="120" id="th4"/><label for="th4">5 days</label></div>
    <div><input type="radio" name="tempHours" value="26" id="th3"/><label for="th3">26 hours</label></div>
    <div><input type="radio" name="tempHours" value="10" id="th2"/><label for="th2">10 hours</label></div>
    <div><input type="radio" name="tempHours" value="1" id="th1"/><label for="th1">Last hour</label></div>
  </div>
</div>
