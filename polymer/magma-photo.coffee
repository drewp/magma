Polymer 'magma-photo',
  refreshSec: null

  periodicReload: () ->
    uri = @attributes['uri'].value
    httpsBase = uri.replace(/^http/, "https")
    @src = httpsBase + "?size=medium"
    @photoPage = httpsBase + "/page"
    @facts = "..."
    $.getJSON httpsBase + "/facts", (f) =>
      @facts = JSON.stringify(f)
      

  resize: (w, h) ->
    [@imgWidth, @imgHeight] = [w, h]
    