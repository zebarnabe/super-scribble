# Introduction #

Mix tool allows the mixing of a starting color to the color selected, creating gradients and similar effects.

It belongs to a class of tools that allow for changes in proprieties of the drawing stroke during it's execution. The propriety changed it's color.

Other proprieties possible to be changed by this kind of tools, but not by this tool, are the size and opacity. The creation of this tools would require a rebuild of the current graphical interface.

# Details #

While it's usage is simple, there are some differences when relating it to similar tools/brushes.

An initial color is picked when putting the stylus down, this color it's not an average of the colors on the brush size, but the exact pixel color on the image data equivalent to the position of the stylus. This could lead to unexpected results if there is a single white pixel that was picked and it's surrounded by black pixels.

The mix slider allows one to select how much touch events are needed to reach full color, determining the length of how long the colors are mixing.

The color change it's linear, however speeding up, or slowing down, the stylus stroke may lead to non linear gradients.

Mix tool supports opacity feature, however, the opacity will be applied evenly, meaning that there is no iteration of opacity. Future support it's possible by changing the graphical interface to allow such ability.