all: 
	curl -T auth.n3 -H "Content-Type: text/rdf+n3" "http://plus:8080/openrdf-sesame/repositories/cmd/statements?context=%3Chttp%3A%2F%2Fbigasterisk.com%2Frdf%2Fauth1%3E"

test:
	(cd commandinference; ../buildout_bin/py `which trial` test_db)
