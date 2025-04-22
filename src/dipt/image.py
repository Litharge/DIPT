from __future__ import annotations
import threading
import time
from functools import partial
from abc import ABC, abstractmethod
from datetime import datetime
import time
from time import monotonic
import logging
from pprint import pprint


import cv2
import numpy as np
from igraph import Graph


from dipt.utils import nested_dict_to_edges, rename_nodes_to_ids


class DisplayException(Exception):
    pass


class ImageTool:
    def add_child(self, to_add):
        self.children.append(to_add)

    def notify_children(self):
        """Notify my children that I have changed"""
        for child in self.children:
            child.parent_changed = True
            child.notify_children()

    def check_if_changed(self):
        while True:
            if self.parent_changed:
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

        self.window_title = new_title + self.window_title_tree_component

    def get_desc_dict(self):

        if len(self.children) > 0:
            return {child.window_name: child.get_desc_dict() for child in self.children}
        else:
            return {}

    def get_new_window_tree_info(self):
        """Gets a dictionary containing coordinates to move the windows to, in order to form a nice visual tree
        Also returns the mapping from names to numbers for constructing the window title
        """

        # first recursively traverse children to make nested dictionary
        desc_dict = {self.window_name: self.get_desc_dict()}

        # convert nested dictionary to edges
        edges = nested_dict_to_edges(desc_dict)
        numeric_edges, id_to_name, name_to_id = rename_nodes_to_ids(desc_dict, edges)

        # convert numeric edges to positions
        g = Graph(directed=True)
        g.add_vertices(len(id_to_name))
        g.add_edges(numeric_edges)
        layout = g.layout("rt")  # Reingold-Tilford layout

        # build coords dictionary
        coords = {id_to_name[id]: layout[id] for id in id_to_name}

        return coords, name_to_id

    def set_window_positions_recursively(self, tree_coords):
        x = int(tree_coords[self.window_name][0] * 100) + 200
        y = int(tree_coords[self.window_name][1] * 100) + 10
        cv2.moveWindow(self.window_name, x, y)
        for child in self.children:
            child.set_window_positions_recursively(tree_coords)

    def set_window_title_tree_component_recursively(self, name_to_id, ancestor_lineage):
        id_of_current = name_to_id[self.window_name]
        if ancestor_lineage == "":
            self.window_title_tree_component = str(id_of_current)
        else:
            self.window_title_tree_component = ancestor_lineage + "." + str(id_of_current)

        cv2.setWindowTitle(self.window_name, self.window_name + " " + self.window_title_tree_component)

        for child in self.children:
            child.set_window_title_tree_component_recursively(name_to_id, self.window_title_tree_component)


    def display_loop(self, refresh_ms=100):
        """
        Frames refresh each self.refresh_ms miliseconds or longer
        """
        tree_coords, name_to_id = self.get_new_window_tree_info()

        self.set_window_positions_recursively(tree_coords)

        self.set_window_title_tree_component_recursively(name_to_id, "")

        while True:
            # todo: should this line be here?
            #cv2.setWindowTitle(self.window_name, self.window_title + "test test")

            old_time = int(monotonic() * 1000)

            self.display_recursively()

            new_time = int(monotonic() * 1000)
            diff = new_time - old_time

            k = cv2.waitKey(refresh_ms - diff)
            if k == ord("q"):
                break
            if k == ord("r"):
                #self.notify_children()
                self.update_matrix()

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

        # window_title is what is displayed
        self.window_title = "Image not initialised"

        self.window_title_tree_component = ""

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

        start = time.thread_time()

        self.matrix_operation()

        self.elapsed = time.thread_time() - start

        if self.should_log_duration:
            self.logger.info(f"Time for <{self.window_name}> to update matrix: {self.elapsed} seconds")

        with self.matrix_lock:
            self.image = self.buffer_image

    def bar_changed(self, to_change, val):
        setattr(self, to_change, val)

        self.update_matrix()

    def __init__(self, input_image: ImageTool, window_name, should_log_duration=False):
        super().__init__(input_image, window_name)

        # set up logger (thread safe unlike print)
        formatter = logging.Formatter('%(message)s')
        self.logger = logging.getLogger(self.window_name)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.DEBUG)

        self.should_log_duration = should_log_duration

        self.elapsed = 0

        self.buffer_image = None

        bar_vars = [v for v in vars(self) if v[-4:] == "_val"]
        bar_vars_max = {v: vars(self)[v + "_max"] for v in bar_vars}
        bar_vars_initial = {v: vars(self)[v] for v in bar_vars}

        self.partial_callbacks = {}
        for var_name in bar_vars_max:
            cv2.createTrackbar(var_name, self.window_name, bar_vars_initial[var_name], bar_vars_max[var_name],
                               partial(self.bar_changed, var_name))

        all_zero = not any([bar_vars_initial[v] for v in bar_vars_initial])

        # if there are no trackbars created, then update_matrix is not called until a change in the parent is detected.
        # also, if the trackbar values are initialised at 0, then it appears the callback does not run either
        # So, manually call update_matrix here
        if len(bar_vars) == 0 or all_zero:
            self.update_matrix()


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

    def update_matrix(self):
        self.notify_children()
