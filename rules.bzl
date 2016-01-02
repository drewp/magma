# def jade(name, visibility=None):
#   native.genrule(
#       name = name,
#       outs = [name.replace('.jade', '.html')],
#       cmd = '$(location node_modules/jade/bin/jade.js) --pretty < $(SRCS) > $@',
#       visibility = visibility,
#   )

def _impl(ctx):
  # You may use print for debugging.
  print("This rule does nothing")

empty = rule(implementation=_impl)

def macro(name, visibility=None):
  # Creating a native genrule.
  native.genrule(
      name = name,
      outs = [name + '.txt'],
      cmd = 'echo hello > $@',
      visibility = visibility,
  )
