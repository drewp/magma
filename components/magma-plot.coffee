mixedCaseFromDashed = (s) -> s.replace(/-(.)/, (m) -> m[1].toUpperCase())
kv = (o) -> mixedCaseFromDashed(o.name) + "=" + encodeURIComponent(o.value)

computedTarget = (which) ->
  switch which
    when 'houseCpu'
      parts = []
      for host in ['bang', 'dash']
        cpuCount = 4
        for i in [0...cpuCount]
          parts.push('perSecond(collectd.'+host+'.cpu-'+i+'.cpu-system)')
      'sumSeries(' + parts.join(',') + ')'
      

titleClearancePx = 6

Polymer
  is: 'magma-plot'
  behaviors: [magma.RefreshingWidgetBehavior]
  properties:
    title: {type: String, notify: true}
  refreshSec: 60 * 10

  periodicReload: () ->
    @params = @paramsFromAttrs(@attributes)
    @salt = Math.round((+new Date()) / (1000 * @refreshSec))    

  paramsFromAttrs: (attrs) =>
    others = []
    targets = []

    others.push({name: 'margin', value: '6'})
    others.push({name: 'fontSize', value: '9'})
    for a, v of attrs
      if v.name?.match(/^target/)
        targets.push(v.value)
      else if v.name == 'title'
        @title = v.value
      else if v.name == 'computed-target'
        targets.push(computedTarget(v.value))
      else if v.name? and v.value?
        others.push(v)
    ("target="+encodeURIComponent(t) for t in targets).concat(
       kv(o) for o in others).join('&')
                  
  resize: (w, h) ->
    [@imgWidth, @imgHeight] = [w, h - (if @title then titleClearancePx else 0)]
    