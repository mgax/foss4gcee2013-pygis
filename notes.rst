Speaker notes
=============

why this
~~~~~~~~
- doing the same thing 50 times in a GUI tool is no fun; let's script it!
- if you're gonna learn a language, might as well be python
- gis tools tend to work well with python (lots of bindings)
- other options available (shell scripts, C/C++, java, c#)


the project
~~~~~~~~~~~
- people in the cities suddenly discover a love for unspoiled nature
- a fixed % go hiking each weekend, evenly distributed to nearby parks
- analyze and visualize the impact on parks: density and origin of visitors
- the plan:

  - calculate park & city centroids
  - calculate geodetic distances; keep nearby parks
  - join with non-spatial data (population table)
  - get data from postgis
  - determine county borders
  - load the result in qgis


workshop framing
~~~~~~~~~~~~~~~~
- we only show very simple processing, focusing on data in/out
- split the code into functions; more flexible than shell scripting
- using raw osgeo live disk; do try this at home
- working in linux, using a decent text editor, run code in terminal
- planning to write ~150 lines of code in 15 steps; miss one and the next
  don't make sense; please ask for help


general tips
~~~~~~~~~~~~
- gedit config:

  - display line numbers
  - highlight matching brackets
  - 4 spaces per tab
  - indent with spaces
  - enable automatic indentation

- gedit plugins:

  - draw spaces
  - smart spaces
  - code comment

- about python

  - designed to be readable
  - not going to explain much at first; it's easy to figure out
  - whitespace matters; indent 4 spaces
  - comments start with #

- keep qgis open
- the setup


final
~~~~~
- we're keeping data in memory. this works because our datasets are small.
- we write main() and other functions so we can use this code as a module
  in another script; the functions are reusable!
- python2 vs python3
