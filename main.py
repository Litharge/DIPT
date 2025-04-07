"""Gross outline experiment"""

from __future__ import annotations
import threading
import time

import cv2
import numpy as np

original_image = cv2.imread("strawberry_2.png", cv2.IMREAD_COLOR_BGR)

hls = cv2.cvtColor(original_image, cv2.COLOR_BGR2HSV)

# the hue channel is in the range 0-179, referring to angle on the colour wheel divided by 2
hue = hls[:,:,0]

print(hue.max())

# convert to uint8 range (0-255), also rotate by 128 to place the discontinuity at the blue end
hue_2 = ((hue * (256/180)) + (128)).astype(np.uint8)

print(f"{hue_2.max()=}")
print(type(hue[0][0]))

hue_2 = hue_2.astype(np.uint8)




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
            print("checking", self)
            if self.parent_changed:
                print("parent changed, updating")
                # todo: actually just update the array
                #  imshow() then needs to be run in the main thread loop
                self.update_matrix()
                self.parent_changed = False
            time.sleep(1)

    def update_matrix(self):
        pass

    def get_image(self):
        with self.matrix_lock:
            return self.image

    def __init__(self, input_image: np.ndarray | ImageTool):
        self.image = None

        self.children = []

        self.parent_changed = False

        self.matrix_lock = threading.Lock()

        print(f"{type(input_image)=}")

        if isinstance(input_image, np.ndarray):
            """In the base case, store the input image"""
            self.input = input_image
        else:
            self.input = input_image

            # input_image is the parent in the tree, so we want changes to cascade down
            input_image.add_child(self)

        t = threading.Thread(target=self.check_if_changed)
        t.start()



class SimpleImage(ImageTool):
    def __init__(self, input_image: np.ndarray):
        super().__init__(input_image)
        self.image = self.input

    def display(self):
        cv2.imshow("Simple", self.get_image())


print("Creating hue_2")
hue_2 = SimpleImage(hue_2)
print("Created")


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
        with self.matrix_lock:
            self.image = np.where((self.input.get_image() > self.hue_min) & (self.input.get_image() < self.hue_max), 255, 0).astype(
                np.uint8)

    def display(self):
        cv2.imshow("Hue Boundary", self.get_image())
        #for image_tool in self.children:
        #    image_tool.update_view()

    def __init__(self, input_image: ImageTool):
        super().__init__(input_image)
        self.hue_min = 126
        self.hue_max = 141

        self.image = None

        cv2.namedWindow("Hue Boundary")

        cv2.createTrackbar("min", "Hue Boundary", self.hue_min, 255, self.min_changed)
        cv2.createTrackbar("max", "Hue Boundary", self.hue_max, 255, self.max_changed)



hue_band = HueBoundaryAdjuster(hue_2)



class NoiseRemover(ImageTool):
    """Does erosion"""
    def __init__(self, input_image: ImageTool):
        super().__init__(input_image)
        self.dilation_value = 0

        self.image = None
        #self.input = input_image


    def erosion_changed(self, val):
        self.erosion_radius = val

        self.update_matrix()

    def update_matrix(self):
        self.notify_children()
        with self.matrix_lock:
            ellipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                                (2 * self.erosion_radius - 1, 2 * self.erosion_radius - 1))
            self.image = cv2.erode(self.input.get_image(), ellipse)

    def display(self):
        cv2.imshow("Eroded", self.get_image())

        #for image_tool in self.children:
        #    image_tool.update_view()


# NoiseRemover is actually not suitable, the
#red_noise_remover = NoiseRemover(hue_band.image)

class HoleRemover(ImageTool):

    def remove_holes_changed(self, val):
        self.remove_holes = val

        self.update_matrix()

    def update_matrix(self):
        self.notify_children()
        with self.matrix_lock:
            contours, _ = cv2.findContours(self.input.get_image(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            # create a 3-channel array with the same height and width as input image
            # todo: make this a helper function
            three_channel = np.zeros_like(self.input.get_image())
            three_channel = three_channel[:, :, np.newaxis]
            three_channel = np.repeat(three_channel, 3, axis=2)

            print(f"{len(contours)}")

            line_width = -1 if self.remove_holes else 1

            for ct in contours:
                self.image = cv2.drawContours(three_channel, [ct], 0, (0, 255, 0), line_width)



    def display(self):
        cv2.imshow(self.window_name, self.get_image())

        # todo: change this to set the children to white + set children "ancestor_changed" variable to True
        #  also add a timer to update the display if ancestor_changed is True, and set ancestor_changed to
        #for image_tool in self.children:
        #    image_tool.update_view()
        #super().notify_children()

    def __init__(self, window_name: str, input_image: ImageTool):
        super().__init__(input_image)
        #self.input_image = input_image.image
        self.image = None
        self.window_name = window_name

        self.remove_holes = 1

        cv2.namedWindow(self.window_name)

        cv2.createTrackbar("Remove Holes", self.window_name, self.remove_holes, 1, self.remove_holes_changed)


hole_filled = HoleRemover("hole filled", hue_band)

print(f"{hue_band.children=}")


#cv2.imshow("Hue 2", hue_2.image)
cv2.imshow("Original", original_image)

while True:
    hue_band.display()
    hole_filled.display()

    k = cv2.waitKey(1000)
    if k == ord("q"):
        break
    print("loop")


cv2.destroyAllWindows()
