Polymer 'magma-plot',
  refreshSec: 60 * 10

  periodicReload: () ->
    @params = @paramsFromAttrs(@attributes)
    @salt = Math.round((+new Date()) / (1000 * @refreshSec))    

  paramsFromAttrs: (attrs) =>
    others = []
    targets = []
    for a, v of attrs
      if v.name?.match(/^target/)
        targets.push(v.value)
      else if v.name? and v.value?
        others.push(v)
    ("target="+encodeURIComponent(t) for t in targets).concat(
      o.name
        .replace('ymax', 'yMax')
        .replace('areamode', 'areaMode') +
        "=" + encodeURIComponent(o.value) for o in others).join('&')
                  
  resize: (w, h) ->
    [@imgWidth, @imgHeight] = [w, h]
    