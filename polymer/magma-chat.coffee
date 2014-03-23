Polymer 'magma-chat',
  history: []
  historyRevision: null
  
  ready: () ->
    console.log("chat ready")
    @socket = new ReconnectingWebSocket('ws://dash:3002/chat')
    @socket.onmessage = @onMessage.bind(this)
    @newMsg = "writing..."
    
  sendLine: (msg) ->
    row = {type: 'newLine', uri: @newUri(), msg: msg, clientTime: +new Date()}
    @asyncFire('newLine', {msg: row})
    @sendWithRetry(row)
    console.log('send')

  layoutRow: (row) ->
    # redo row.layout
    row.layout = 
      classes: 'mine'

  sendWithRetry: (js) ->
    try
      @socket.send(JSON.stringify(js))
    catch e
      console.log("websocket send failed, retrying")
      setTimeout((=> @sendWithRetry(js)), 1000)   

  newUri: () ->
    ("http://bigasterisk.com/chat/" +
     (+new Date()) +
     "-" +
     (Math.random().toString(16).substr(2,4)))

  submitLine: (ev) ->
    console.log('sl', @newMsg)
    event.preventDefault()
    @sendLine(@newMsg)
    @newMsg = ''

  newMsgChanged: (old, newValue) ->
    console.log('nmc', newValue)

  reloadHistory: () ->
    @sendWithRetry({req: 'reloadHistory'})
    
  onMessage: (msg) ->
    console.log('onmsg', msg)
    msg = JSON.parse(msg.data)
    if msg.type == 'history'
      @history = msg.history
      @layoutRow(r) for r in @history
      console.log('assigned', @history.length)
    # we could receive appends in many cases, but this sample doesn't cover the case that prev/last match but a past line's data was edited. I think this should be 'patchHistory' which says how to get from past version to this one (often an append but sometimes more edits)
    #if msg.type == 'appendHistory'
    #  if msg.prev.uri != @history[@history.length - 1].uri
    #    @reloadHistory()
    #  else
    #    @history.push(msg.last)
        