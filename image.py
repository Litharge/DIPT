"""Gross outline experiment"""

from __future__ import annotations
import threading
import time
from functools import partial
from abc import ABC, abstractmethod
from datetime import datetime
import time
from time import monotonic


import cv2
import numpy as np


class DisplayException(Exception):
    pass


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

    def display_recursively(self):
        for child in self.children:
            child.display_recursively()

        new_title = self.window_name

        try:
            cv2.imshow(self.window_name, self.get_image())
        except Exception as e:
            if self.display_blank_on_error:
                new_title = "Error displaying image"
            else:
                raise DisplayException("Error displaying with cv2.imshow in base display method. "
                      "Check that your input image is not None.")

        cv2.setWindowTitle(self.window_name, new_title)

    def display_loop(self, refresh_ms=100):
        """
        Frames refresh each self.refresh_ms miliseconds or longer
        """
        while True:
            old_time = int(monotonic() * 1000)

            self.display_recursively()

            new_time = int(monotonic() * 1000)
            diff = new_time - old_time

            k = cv2.waitKey(refresh_ms - diff)
            if k == ord("q"):
                break

        self.terminate_recursively()

        cv2.destroyAllWindows()

    def __init__(self, input_image: np.ndarray | ImageTool, window_name):
        """
        Creates the named window, and creates parent/child relations
        :param input_image: the parent image
        :param window_name: the name of the named window to create
        """
        self.window_name = window_name
        cv2.namedWindow(self.window_name)

        self.display_blank_on_error = True

        self.image = None
        self.matrix_lock = threading.Lock()

        self.children = []

        self.input = input_image
        self.parent_changed = False

        if isinstance(input_image, ImageTool):
            # input_image is the parent in the tree, so we want changes to cascade down
            input_image.add_child(self)

        self.kill_thread = threading.Event()

        self.thread = threading.Thread(target=self.check_if_changed)
        self.thread.start()


class CustomImageTool(ImageTool, ABC):
    @abstractmethod
    def matrix_operation(self):
        pass

    def update_matrix(self):
        self.notify_children()

        self.matrix_operation()

        with self.matrix_lock:
            self.image = self.temp_image

    def bar_changed(self, to_change, val):
        setattr(self, to_change, val)

        self.update_matrix()

    def __init__(self, input_image: ImageTool, window_name):
        super().__init__(input_image, window_name)

        self.temp_image = None

        bar_vars = [v for v in vars(self) if v[-4:] == "_val"]
        bar_vars_max = {v: vars(self)[v + "_max"] for v in bar_vars}
        bar_vars_initial = {v: vars(self)[v] for v in bar_vars}

        self.partial_callbacks = {}
        for var_name in bar_vars_max:
            cv2.createTrackbar(var_name, self.window_name, bar_vars_initial[var_name], bar_vars_max[var_name],
                               partial(self.bar_changed, var_name))


class SimpleImage(ImageTool):
    """Takes as input an ndarray image. Does nothing other than store and display the input image. The object is a
    valid input to any other ImageTool subclass. It is always the root element in a DIPT tree.
    """
    def __init__(self, input_image: np.ndarray, window_name):
        """
        :param input_image: ndarray image
        """
        super().__init__(input_image, window_name)
        self.image = self.input
