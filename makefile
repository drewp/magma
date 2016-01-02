.PHONY: build
build: fix_some_path_bug
	node_modules/jastyco/bin/jastyco -b

.PHONY: build-watch
build-watch: fix_some_path_bug build
	node_modules/jastyco/bin/jastyco

fix_some_path_bug:
	@mkdir -p build/components/
	@ln -nsf components build/mponents
