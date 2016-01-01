REPO = "http://bang:8080/openrdf-sesame/repositories/cmd/statements?context=%3Chttp%3A%2F%2Fbigasterisk.com%2Fmagma%2Fsource%2F"
all: 
	cwm /my/site/magma/config.n3 --ntriples | curl -T - -H "Content-Type: text/plain" $(REPO)magmaConfig%3E | more
	cwm /my/site/magma/auth.n3 --ntriples | curl -T - -H "Content-Type: text/plain" $(REPO)auth%3E | more
	cwm /my/proj/room/devices.n3 --ntriples | curl -T - -H "Content-Type: text/plain" $(REPO)devices%3E | more
	cwm /my/proj/openid_proxy/access.n3 --ntriples | curl -T - -H "Content-Type: text/plain" $(REPO)access%3E | more

test:
	(cd commandinference; ../buildout_bin/py `which trial` test_db)
