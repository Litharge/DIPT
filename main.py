import cv2
import numpy as np

from image import ImageTool, SimpleImage, HueBoundaryAdjuster, NoiseRemover, HoleRemover, HueImage


original_image = cv2.imread("strawberry_2.png", cv2.IMREAD_COLOR_BGR)

initial = SimpleImage(original_image)

hue = HueImage(initial)

hue_band = HueBoundaryAdjuster(hue)

# NoiseRemover is actually not suitable, the
#red_noise_remover = NoiseRemover(hue_band.image)

hole_filled = HoleRemover("hole filled", hue_band)

print(f"{hue_band.children=}")

#cv2.imshow("Hue 2", hue.image)
cv2.imshow("Original", original_image)

while True:
    initial.display()
    hue.display()
    hue_band.display()
    hole_filled.display()

    k = cv2.waitKey(1000)
    if k == ord("q"):
        break
    print("loop")

initial.terminate_recursively()


cv2.destroyAllWindows()
