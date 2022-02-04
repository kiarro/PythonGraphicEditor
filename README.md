# Paint Py

Simple graphic editor.

All draw options realized on pixel level.

Draw options:

- pen
- line
- rectangle (square if Shift down)
- ellipse (round if Shift down)
- fill

Also:

- select and transform rectangle area
- move canvas
- choose color
- choose brush width
- save image
- zoom

## Brushes

Brush object contain all brush pixels and borders of brush.

Runtime brush create.

Brush might be any figure with vertical and horizontal symmetry.

## Draw algorithms

- pen: draw lines between consecutive points
- line: draw line between two points; 1 pixel width: Bresenham's line algorithm; >1 pixel width: draw brush border in all points of 1 pixel line
- rectangle: draw 2 horizontal and 2 vertical lines; depends on brush size but not brush form
- ellipse: draw ellipse inscribed in a rectangle; modified Bresenham's round algorithm; depends on brush form
- fill: Flood Fill Algorithm
