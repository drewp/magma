Polymer 'magma-chat',
  history: []
  historyRevision: null
  foaf: null
  mePrompt: "Me"
  
  ready: () ->
    console.log("chat ready")
    @socket = new ReconnectingWebSocket(
      window.location.origin.replace(/^https:/, 'wss:').replace(/^http:/, 'ws:') + 
      '/magma/chat/')
    @socket.reconnectInterval = 2000;
    @socket.onmessage = @onMessage.bind(this)
    @newMsg = ""
    
  sendLine: (msg) ->
    row = {uri: @newUri(), t: (new Date()).toJSON(), html: msg}
    @asyncFire('newLine', row)
    @sendWithRetry({type: 'post', row: row})
    console.log('send')

  layoutRow: (row) ->
    # redo row.layout
    row.layout = 
      classes: if @foaf == row.creator then 'mine' else 'friend'
      shortTime: moment(row.t).format('ddd H:mm:ss')
      shortSender: @shortName(row.creator)

  shortName: (uri) ->
    switch uri
      when "http://bigasterisk.com/foaf.rdf#drewp" then "Drew"
      when "http://bigasterisk.com/kelsi/foaf.rdf#kelsi" then "Kelsi"
      else uri

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
    @sendWithRetry({type: 'reloadHistory'})
    
  onMessage: (msg) ->
    console.log('onmsg', msg)
    msg = JSON.parse(msg.data)
    if msg.type == 'history'
      @foaf = msg.you
      @mePrompt = @shortName(@foaf)
      @history = msg.history
      @layoutRow(r) for r in @history
      console.log('assigned', @history.length)
    if msg.type == 'append' # temporary type
      @history.push(msg.row)
      
    # needs to be after the add
    setTimeout(( => @$.histArea.scrollTop = @$.histArea.scrollHeight), 100)
    # we could receive appends in many cases, but this sample doesn't cover the case that prev/last match but a past line's data was edited. I think this should be 'patchHistory' which says how to get from past version to this one (often an append but sometimes more edits)
    #if msg.type == 'appendHistory'
    #  if msg.prev.uri != @history[@history.length - 1].uri
    #    @reloadHistory()
    #  else
    #    @history.push(msg.last)
        