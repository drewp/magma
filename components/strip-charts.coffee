Polymer
  is: 'strip-charts'
  properties:
    title: {type: String, notify: true}

  ready: () ->
    @ctx = @$.c1.getContext('2d')
    @now = Date.now() / 1000

  xForTime: (t) ->
    t0 = @now - 86400
    return 200 * (t - t0) / (@now - t0)

  onData: (ev) ->
    result = ev.target.lastResponse.results[0]
    return if !result.series || result.series.length == 0
    series = result.series[0]

    y = 0
    if series.columns.name == 'state'
      y = 10
    
    @ctx.fillStyle = 'green'
    last = [0, 0]
    for [t, v] in series.values
      if last[1] == 1
        x1 = @xForTime(last[0])
        x2 = @xForTime(t)
        if x2 > 0
          @ctx.fillRect(x1, y, x2 - x1, y + 10)
      last = [t, v]
    if last[1] == 1
      x1 = @xForTime(last[0])
      x2 = @xForTime(Date.now() / 1000)
      @ctx.fillRect(x1, y, x2 - x1, y + 10)