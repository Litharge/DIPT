# DIPT

Digital Image Processing Tree (DIPT) is an easy to use package for the creation of observable digital
image processing pipelines. The user can quickly define new operations and add them to pipelines in a tree-like
structure, where the root is the original image.

## Installation

Clone the repository

Install locally with pip, pipenv etc

    python -m pipenv install -e <path to DIPT>

## Core Usage

Core usage handles cv2 windowing, rendering and descendant updates for you.

See samples/core_usage.py for an example of a simple tree

### Defining an Operation

Override CustomImageTool to define a new, adjustable operation e.g. adjustable noise removal

Simply override the \_\_init\_\_ and matrix_operation methods

The \_\_init\_\_ method contains any slider variables you intend to use in your matrix_operation, as well as the maximum 
values of those slider variables. 

The matrix_operation method contains your operation (e.g. morphological, convolutional). Get the contents of 
the parent node with self.input.get_image(), perform your operation and save your result in self.buffer_image.

You must use self.input.get_image() and not self.input.image as the matrix may be accessed in another thread, get_image
opens the lock.

### Building your Pipeline Tree

Create the root node by creating an instance of SimpleImage, passing in your original image as an ndarray, as well as a unique window name.
Define descendants by creating instances of your operations and passing the parent node, as well as a unique window name.
Begin rendering by calling `display_loop` on your root element

## Advanced Usage

Alternatively, Advanced Usage gives you more control, while still facilitating tree-like updating od descendants

See samples/advanced_usage.py for an example of a simple tree

### Creating a New Subclass

You can create subclasses of ImageTool directly, giving you more control over cv2 windowing and the tree structure

## Notes for Future Improvements

Package on PyPi coming soon

I would like for the cv2.imshow method to be called in each thread, as the children are called recursively, however
this is (for the present at least) impossible, due to cv2.imshow not being thread safe. Therefore, in the current
implementation, the display method for each instance is called in a render loop in a single thread.