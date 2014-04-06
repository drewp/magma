Polymer 'magma-plot',
  imgWidth: 100
  imgHeight: 100
  salt: 0
  refreshSec: 60 * 10
  attached: () ->
    @_changeWhenVisible()
    
    window.addEventListener('resize', (() =>
      @_onResize()
    ))
    @_onResize()

  _onResize: () ->
    @_changeWhenVisible =>
      @resize(@$.top.offsetWidth, @$.top.offsetHeight)

  _changeWhenVisible: (cb) ->
    if (document.hidden ||
        document.mozHidden ||
        document.msHidden ||
        document.webkitHidden)
      setTimeout(@_changeWhenVisible, 5000)
      return
    @periodicReload()
    setTimeout(@_changeWhenVisible, @refreshSec * 1000)


  periodicReload: () ->
    @salt = Math.round((+new Date()) / (1000 * @refreshSec))    
      
  resize: (w, h) ->
    [@imgWidth, @imgHeight] = [w, h]
    