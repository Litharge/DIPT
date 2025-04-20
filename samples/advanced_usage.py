import cv2
import numpy as np


from image import ImageTool, SimpleImage


class HueImage(ImageTool):
    def __init__(self, input_image, window_name):
        super().__init__(input_image, window_name)

        self.discontinuity = 128

        cv2.createTrackbar("min", self.window_name, self.discontinuity, 255, self.discontinuity_changed)

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

    def __init__(self, input_image: ImageTool, window_name):
        super().__init__(input_image, window_name)

        self.hue_min = 126
        self.hue_max = 141

        cv2.createTrackbar("min", self.window_name, self.hue_min, 255, self.min_changed)
        cv2.createTrackbar("max", self.window_name, self.hue_max, 255, self.max_changed)


class NoiseRemover(ImageTool):
    """Does erosion"""
    def __init__(self, input_image: ImageTool, window_name):
        super().__init__(input_image, window_name)
        self.erosion_radius = 0

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


    def __init__(self, input_image: ImageTool, window_name: str,):
        super().__init__(input_image, window_name)

        self.remove_holes = 1

        cv2.createTrackbar("Remove Holes", self.window_name, self.remove_holes, 1, self.remove_holes_changed)


original_image = cv2.imread("strawberry_2.png", cv2.IMREAD_COLOR_BGR)

initial = SimpleImage(original_image, "initial")

hue = HueImage(initial, "hue")

hue_band = HueBoundaryAdjuster(hue, "hue band")

# NoiseRemover is actually not suitable, the
#red_noise_remover = NoiseRemover(hue_band.image)

hole_filled = HoleRemover(hue_band, "hole filled")

initial.display_loop()
