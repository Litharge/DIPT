# DIPT

Digital Image Processing Tree (DIPT) is an easy to use package for the creation of observable digital
image processing pipelines. The user can quickly define new operations and add them to pipelines in a tree-like
structure, where the root is the original image.

## Installation

Clone the repository

## Core Usage

Core usage handles cv2 windowing, rendering and descendant updates for you.

### Defining an Operation

Override CustomImageTool to define a new, adjustable operation e.g. adjustable noise removal

Simply override the \_\_init\_\_ and matrix_operation methods

The \_\_init\_\_ method contains any slider variables you intend to use in your matrix_operation, as well as the maximum 
values of those slider variables. 

The matrix_operation method contains your operation (e.g. morphological, convolutional). Get the contents of 
the parent node with self.input.get_image(), perform your operation and save your result in self.buffer_image

### Building your Pipeline Tree

Create the root node by creating an instance of SimpleImage, passing in your original image as an ndarray, as well as a unique window name.
Define descendants by creating instances of your operations and passing the parent node, as well as a unique window name.
Begin rendering by calling `display_loop` on your root element

## Advanced Usage

Alternatively, Advanced Usage gives you more control, while still facilitating tree-like updating od descendants

### Creating a New Subclass

You can create subclasses of ImageTool directly, giving you more control over cv2 windowing and the tree structure

## Functional Requirements

1. The package must support the creation of a tree-like structure to join together Digital Image Processing steps
   1. Each node on the tree must get the state of its parent when that parent updates
   2. The operation of each node on the tree must be user-adjustable via sliders 
2. The package must 

## Non-Functional Requirements
1. Balance between flexibilty and ease of implementation for the user
2. Facilitate observability of intermediate states in the pipeline
3. Facilitate adjustability of operations in the pipeline, both in code and at run time

## Notes for Future Improvements

Package on PyPi coming soon

I would like for the cv2.imshow method to be called in each thread, as the children are called recursively, however
this is (for the present at least) impossible, due to cv2.imshow not being thread safe. Therefore, in the current
implementation, the display method for each instance is called in a render loop in a single thread.