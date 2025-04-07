import cv2
import numpy as np

from image import ImageTool, SimpleImage, HueBoundaryAdjuster, NoiseRemover, HoleRemover


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


hue_2 = SimpleImage(hue_2)

hue_band = HueBoundaryAdjuster(hue_2)

# NoiseRemover is actually not suitable, the
#red_noise_remover = NoiseRemover(hue_band.image)

hole_filled = HoleRemover("hole filled", hue_band)

print(f"{hue_band.children=}")

#cv2.imshow("Hue 2", hue_2.image)
cv2.imshow("Original", original_image)

while True:
    hue_2.display()
    hue_band.display()
    hole_filled.display()

    k = cv2.waitKey(1000)
    if k == ord("q"):
        break
    print("loop")


cv2.destroyAllWindows()
