import numpy as np
import cv2
from datetime import datetime

from dipt.image import SimpleImage, CustomImageTool


class HueImage(CustomImageTool):
    def __init__(self, input_image, window_name, **kwargs):
        self.discontinuity_val = 128

        self.discontinuity_val_max = 255

        super().__init__(input_image, window_name, **kwargs)

    def matrix_operation(self):
        hls = cv2.cvtColor(self.input.get_image(), cv2.COLOR_BGR2HSV)

        # the hue_channel channel is in the range 0-179, referring to angle on the colour wheel divided by 2
        hue_channel = hls[:, :, 0]

        # convert to uint8 range (0-255), also rotate by 128 to place the discontinuity at the blue end
        self.buffer_image = ((hue_channel * (256 / 180)) + self.discontinuity_val).astype(np.uint8)


class HueBoundaryAdjuster(CustomImageTool):
    def __init__(self, input_image, window_name, **kwargs):
        self.hue_min_val = 112
        self.hue_max_val = 144

        self.hue_min_val_max = 255
        self.hue_max_val_max = 255

        super().__init__(input_image, window_name, **kwargs)

    def matrix_operation(self):
        self.buffer_image = np.where(
            (self.input.get_image() > self.hue_min_val) & (self.input.get_image() < self.hue_max_val),
            255,
            0).astype(np.uint8)


class NoiseRemover(CustomImageTool):
    def __init__(self, input_image, window_name, **kwargs):
        self.erosion_dilation_radius_val = 0

        self.erosion_dilation_radius_val_max = 5

        super().__init__(input_image, window_name, **kwargs)

    def matrix_operation(self):
        if self.erosion_dilation_radius_val > 0:
            ellipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                                (2 * self.erosion_dilation_radius_val - 1,
                                                 2 * self.erosion_dilation_radius_val - 1)
                                                )
            eroded = cv2.erode(self.input.get_image(), ellipse)
            self.buffer_image = cv2.dilate(eroded, ellipse)
        else:
            self.buffer_image = self.input.get_image()


class HoleRemover(CustomImageTool):
    def matrix_operation(self):
        contours, _ = cv2.findContours(self.input.get_image(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # create a 3-channel array with the same height and width as input image
        three_channel = np.zeros_like(self.input.get_image())
        three_channel = three_channel[:, :, np.newaxis]
        three_channel = np.repeat(three_channel, 3, axis=2)

        line_width = -1

        self.buffer_image = None
        for ct in contours:
            self.buffer_image = cv2.drawContours(three_channel, [ct], 0, (0, 255, 0), line_width)


original_image = cv2.imread("strawberry_2.png", cv2.IMREAD_COLOR_BGR)

initial = SimpleImage(original_image, "initial image")

hue = HueImage(initial, "hue")

hue_band = HueBoundaryAdjuster(hue, "hue band selection")

hole_filled = HoleRemover(hue_band, "hole filled", should_log_duration=True)

red_noise_remover = NoiseRemover(hue_band, "noise removed", should_log_duration=True)

hole_filled_2 = HoleRemover(red_noise_remover, "hole filled after noise removed", should_log_duration=True)

initial.display_loop(refresh_ms=100)
