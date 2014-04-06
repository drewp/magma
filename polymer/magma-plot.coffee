Polymer 'magma-plot',
  imgWidth: 100
  imgHeight: 100
  salt: 0
  refreshSec: 60 * 10
  attached: () ->
    setInterval((() =>
      @changeWhenVisible =>
        @salt = Math.round((+new Date()) / (1000 * @refreshSec))
    ), @refreshSec * 1000)
    
    @resize()

    window.addEventListener('resize', (() =>
      @resize()
    ))

  resize: () ->
    @changeWhenVisible =>
      elem = @$.top
      @imgWidth = elem.offsetWidth
      @imgHeight = elem.offsetHeight

  changeWhenVisible: (cb) ->
    if (document.hidden ||
        document.mozHidden ||
        document.msHidden ||
        document.webkitHidden)
      setTimeout(@changeWhenVisible, 5000)
      return
    cb()
    