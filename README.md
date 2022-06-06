#Box generator for box or drawer's interiors
## Presentation

When using my box generator ([Github link](https://github.com/thierry7100/GenBox) , the generated interior slots (simple and regular rows and columns) are not always adapted to the need.
And to cover all cases, the number of parameters would be staggering.
So I decided to do it differently.

With this extension, everything starts from a drawing (this is right, Inkscape is there for that). So you need a drawing of the slots you want to make.
Attention this drawing must only be composed of **rectangles** and the only authorized directions are horizontal and vertical. No squares with non-orthogonal sides!

## Installation of the software

It takes the form of an inkscape plugin. <br>
To install it, unzip the .zip. Copy one of the two .inx files (drawerbox.inx if you prefer the English interface, drawerbox_fr.inx for a French interface) plus the two .py files that contain the code. Copy the 3 files (one interface extension.inx, and the two programs, extension .py) into the inkscape extension directory. To know this one, the Edit/Preferences command indicates the path, either of the global directory, or that for you only user. On Linux it's ~/.config/inkscape/extensions for the local directory I use. On Windows, it's in C:\Users\Your Username\AppData\Roaming\inskscape\extensions. <br>
See below for instructions how to use the software.

## Drawing input

I recommend doing everything with Inkscape's rectangle tool (required in this version). The best is to leave the background and not put outlines. With a wood thickness of 3mm, draw rectangles 3mm thick. In this first version, the thickness is also requested by the Inkscape extension, the values ​​**MUST** match.

###Type of boxes supported
The tool is able to generate edge-to-edge connections between orthogonal partitions.

![c](/home/thierry/DrawerBox/Connection1.png "Edge-to-Edge Partition")

I have here drawn each partition with a different color for this example, but the colors have no meaning for this extension.
It is then necessary to correctly align the rectangles. To do this, use the Inkscape functions "align the right edge of the object to the left edge of the anchor" or up and down... For the junctions to be recognized, the right edge of the horizontal partition must coincide with the left edge of the vertical partition (obviously you can swap right and left and horizontal and vertical). The program rounds all coordinates to tenths of mm, rounded values ​​**MUST** match

It is possible to have connections on the right and on the left (overlapping) on ​​a partition. The notches are adapted for this, with half notches, above on the right/top and below on the left/bottom (or ) .

It is also possible to have half timber assemblies with intersecting partitions.

![ ](/home/thierry/DrawerBox/Connection2.png "intersecting partition")

In this case, the partitions must completely cross and "overhang" by at least 0.1mm (program rounding). Otherwise, there will be no junction traced since the connection will not be edge to edge nor through!

You can also have partitions that do not touch each other, in which case there will be no fasteners on the sides.

Here is a slightly more complex example

![ ](/home/thierry/DrawerBox/example.png "Example for box interior")

Here again, the colors are just there to identify the different partitions.

## Using the extension

Once the drawing is done, select it entirely. Only selected rectangles will be processed.
Then in inkscape extensions choose "fablab/box box generator". The following dialog box should appear.

![ ](/home/thierry/DrawerBox/Dialog_en.png "Extension Dialog")

For unit, choose your usual unit (generally mm).
Then define the thickness of the material (here 3mm).
Then the height of the boxes.

The laser beam compensation value is intended to compensate for the thickness of the beam to obtain fairly hard joints, which can hold without glue (at least temporarily). 0.1 mm is a good value for thin wood. For other materials it is to be adjusted.

Finally, you can choose whether or not to draw a bottom on your structure. I advise to do it, it considerably reinforces the realization, but if you are a bit short for the height...

## Assembly

Even for a simple realization, you end up with a certain number of pieces, so you have to be careful when assembling!
I recommend having the original drawing in front of you!
You could use the Inkscape command objects/objects. The generated pieces have the same root name as the rectangle of the original drawing. For example rect1234 will become wallrect1234. 

It seems to me easier to start from the inside of the box. If there are several small pieces, it could be a bit difficult to put it together.
If you have half-height joints, insert the "bottom" parts first, then the top ones. This type of assembly is generally easier to assemble than edge-to-edge ones.

Here is the drawing above

![ ](/home/thierry/DrawerBox/DrawerBox1.jpg "Interior mounted")


## Possible developments

Tell me, or do it yourself...
In that case, don't forget to repost!

