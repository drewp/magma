Polymer 'magma-plot',
  refreshSec: 60 * 10

  periodicReload: () ->
    @from = encodeURIComponent(@attributes['from'].value)
    @targetParams = @targetParamsFromAttrs(@attributes)
    @salt = Math.round((+new Date()) / (1000 * @refreshSec))    

  targetParamsFromAttrs: (attrs) =>
    targets = []
    for a, v of attrs
      if v.name?.match(/^target/)
        targets.push(v.value)
    ("target="+encodeURIComponent(t) for t in targets).join('&')
                  
  resize: (w, h) ->
    [@imgWidth, @imgHeight] = [w, h]
    