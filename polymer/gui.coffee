window.addEventListener 'polymer-ready', (e) ->
  chat = document.querySelector('.chat')
  console.log('found', chat)
  chat.addEventListener 'newLine', (e) ->
    console.log('newLine', e)
  chat.sendLine('newln')
