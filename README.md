# DrawBox

This project implements a quick-and-dirty UI for manually annotating a series of images with bounding boxes.

    python3 DrawBox.py -o output.json images/*.jpg

Boxes can be drawn by simply clicking and dragging. A single box can be selected by clicking or using the <kbd>Tab</kbd> key; this reveals controls for resizing an existing box. Delete a selected box with <kbd>⌫</kbd>. Cycle between images with the <kbd>←</kbd> and <kbd>→</kbd> keys. <kbd>Q</kbd> exits the program.

The JSON output file will be read to load existing boxes, which are matched to the input image files according to their basenames. Each modification will write out a new version. It looks something like this:

```json
{
   "a.jpg": [
      [ 370, 237, 132, 105 ],
      [ 518, 134, 109, 147 ],
      [ 261, 112, 91, 122]
   ],
   "b.jpg": [
      [ 368, 145, 167, 100 ],
      [ 185, 185, 151, 46 ]
   ]
}
```

The boxes are specified in terms of their top-left corner and width and height.
