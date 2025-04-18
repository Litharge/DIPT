"""Gross outline experiment"""

from __future__ import annotations
import threading
import time

import cv2
import numpy as np


class ImageTool:
    def add_child(self, to_add):
        print("adding child", to_add, "to", self)
        self.children.append(to_add)

    def notify_children(self):
        """Notify my children that I have changed"""
        for child in self.children:
            child.parent_changed = True
            child.notify_children()

    def check_if_changed(self):
        while True:
            if self.parent_changed:
                print("parent changed, updating")
                # todo: actually just update the array
                #  imshow() then needs to be run in the main thread loop
                self.update_matrix()
                self.parent_changed = False
            time.sleep(1)

            if self.kill_thread.is_set():
                break

    def update_matrix(self):
        pass

    def get_image(self):
        with self.matrix_lock:
            return self.image

    def terminate_recursively(self):
        """End the matrix update listener thread for self and all descendents"""
        self.kill_thread.set()
        for child in self.children:
            child.terminate_recursively()

    def __init__(self, input_image: np.ndarray | ImageTool):
        self.image = None

        self.children = []

        self.parent_changed = False

        self.matrix_lock = threading.Lock()

        print(f"{type(input_image)=}")

        self.input = input_image

        if isinstance(input_image, ImageTool):
            # input_image is the parent in the tree, so we want changes to cascade down
            input_image.add_child(self)

        self.kill_thread = threading.Event()

        self.thread = threading.Thread(target=self.check_if_changed)
        self.thread.start()


class SimpleImage(ImageTool):
    """Takes as input an ndarray image. Does nothing other than display the image and the object is a valid input to
    any other ImageTool subclass
    """
    def __init__(self, input_image: np.ndarray):
        """
        :param input_image: ndarray image
        """
        super().__init__(input_image)
        self.image = self.input

    def display(self):
        cv2.imshow("Simple", self.get_image())


class HueImage(ImageTool):
    def __init__(self, input_image):
        super().__init__(input_image)

        self.discontinuity = 128

        cv2.namedWindow("Hue")

        cv2.createTrackbar("min", "Hue", self.discontinuity, 255, self.discontinuity_changed)

    def update_matrix(self):
        self.notify_children()

        hls = cv2.cvtColor(self.input.get_image(), cv2.COLOR_BGR2HSV)

        # the hue_channel channel is in the range 0-179, referring to angle on the colour wheel divided by 2
        hue_channel = hls[:, :, 0]

        print(hue_channel.max())

        # convert to uint8 range (0-255), also rotate by 128 to place the discontinuity at the blue end
        hue = ((hue_channel * (256 / 180)) + self.discontinuity).astype(np.uint8)

        with self.matrix_lock:
            self.image = hue.astype(np.uint8)

    def discontinuity_changed(self, val):
        self.discontinuity = val

        self.update_matrix()

    def display(self):
        cv2.imshow("Hue", self.get_image())


# now get pixels in range
class HueBoundaryAdjuster(ImageTool):
    def min_changed(self, val):
        self.hue_min = val

        self.update_matrix()

    def max_changed(self, val):
        self.hue_max = val

        self.update_matrix()

    def update_matrix(self):
        self.notify_children()

        temp_image = np.where((self.input.get_image() > self.hue_min) & (self.input.get_image() < self.hue_max), 255, 0).astype(
                np.uint8)

        with self.matrix_lock:
            self.image = temp_image

    def display(self):
        cv2.imshow("Hue Boundary", self.get_image())
        #for image_tool in self.children:
        #    image_tool.update_view()

    def __init__(self, input_image: ImageTool):
        super().__init__(input_image)

        self.hue_min = 126
        self.hue_max = 141

        cv2.namedWindow("Hue Boundary")

        cv2.createTrackbar("min", "Hue Boundary", self.hue_min, 255, self.min_changed)
        cv2.createTrackbar("max", "Hue Boundary", self.hue_max, 255, self.max_changed)


class NoiseRemover(ImageTool):
    """Does erosion"""
    def __init__(self, input_image: ImageTool):
        super().__init__(input_image)
        self.dilation_value = 0

    def erosion_changed(self, val):
        self.erosion_radius = val

        self.update_matrix()

    def update_matrix(self):
        self.notify_children()

        ellipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                            (2 * self.erosion_radius - 1, 2 * self.erosion_radius - 1))
        temp_image = cv2.erode(self.input.get_image(), ellipse)

        with self.matrix_lock:
            self.image = temp_image

    def display(self):
        cv2.imshow("Eroded", self.get_image())

        #for image_tool in self.children:
        #    image_tool.update_view()


class HoleRemover(ImageTool):

    def remove_holes_changed(self, val):
        self.remove_holes = val

        self.update_matrix()

    def update_matrix(self):
        self.notify_children()

        contours, _ = cv2.findContours(self.input.get_image(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # create a 3-channel array with the same height and width as input image
        # todo: make this a helper function
        three_channel = np.zeros_like(self.input.get_image())
        three_channel = three_channel[:, :, np.newaxis]
        three_channel = np.repeat(three_channel, 3, axis=2)

        print(f"{len(contours)=}")

        line_width = -1 if self.remove_holes else 1

        temp_image = None
        for ct in contours:
            temp_image = cv2.drawContours(three_channel, [ct], 0, (0, 255, 0), line_width)

        with self.matrix_lock:
            self.image = temp_image

    def display(self):
        cv2.imshow(self.window_name, self.get_image())

        # todo: change this to set the children to white + set children "ancestor_changed" variable to True
        #  also add a timer to update the display if ancestor_changed is True, and set ancestor_changed to
        #for image_tool in self.children:
        #    image_tool.update_view()
        #super().notify_children()

    def __init__(self, window_name: str, input_image: ImageTool):
        super().__init__(input_image)

        self.window_name = window_name

        self.remove_holes = 1

        cv2.namedWindow(self.window_name)

        cv2.createTrackbar("Remove Holes", self.window_name, self.remove_holes, 1, self.remove_holes_changed)


