## Core Usage

Core usage handles cv2 windowing, rendering and descendant updates for you.

### Creating a New Subclass


## Advanced Usage

Alternatively, Advanced Usage gives you more control, while still facilitating tree-like updating od descendants

### Creating a New Subclass

You can create subclasses of ImageTool directly, giving you more control over cv2 windowing and the tree structure

Be aware that update_matrix is called only when cv2.createTrackbar is called and when the trackbar value changes.
Therefore, if you do not create a trackbar, your update_matrix will never be called and self.get_image will return
and empty value

## Requirements

1. The package must support the creation of a tree-like structure to join together Digital Image Processing steps

## Notes for Future Improvements

I would like for the cv2.imshow method to be called in each thread, as the children are called recursively, however
this is (for the present at least) impossible, due to cv2.imshow not being thread safe. Therefore, in the current
implementation, the display method for each instance is called in a render loop in a single thread.