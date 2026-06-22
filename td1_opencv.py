import cv2
import numpy as np
image = cv2.imread("image1.png")

cv2.imshow("Etape 3", image)
cv2.waitKey(0)
cv2.destroyWindow("Etape 3")

height, width, channels = image.shape
print("X :", width)
print("Y :", height)

image_resized = cv2.resize(image, (800, 600))
cv2.imwrite("image1_resized.png", image_resized)

cv2.imshow("Etape 5", image_resized)
cv2.waitKey(0)
cv2.destroyWindow("Etape 5")

image_gris = cv2.cvtColor(image_resized, cv2.COLOR_BGR2GRAY)

cv2.imshow("Etape 6", image_gris)
cv2.waitKey(0)
cv2.destroyWindow("Etape 6")

(_, image_nb_120) = cv2.threshold(image_gris, 120, 255, cv2.THRESH_BINARY)
cv2.imshow("Etape 6 seuil 120", image_nb_120)
cv2.waitKey(0)
cv2.destroyWindow("Etape 6 seuil 120")

(_, image_nb_70) = cv2.threshold(image_gris, 70, 255, cv2.THRESH_BINARY)
cv2.imshow("Etape 6 seuil 170", image_nb_70)
cv2.waitKey(0)
cv2.destroyWindow("Etape 6 seuil 70")

for seuil in [50, 100, 150, 200]:
    (_, img_var) = cv2.threshold(image_gris, seuil, 255, cv2.THRESH_BINARY)
    cv2.imshow(f"Etape 7 Seuil {seuil}", img_var)
    cv2.waitKey(0)
    cv2.destroyWindow(f"Seuil = {seuil}")

image_blur = cv2.blur(image_nb_120, (5, 5))
cv2.imshow("Etape 8 Blur", image_blur)
cv2.waitKey(0)
cv2.destroyWindow("Etape 8 Blur")

image_median_blur = cv2.medianBlur(image_nb_120, 5)
cv2.imshow("Etape 8 medianBlur", image_median_blur)
cv2.waitKey(0)
cv2.destroyWindow("Etape 8 medianBlur")

image_gaussian_blur = cv2.GaussianBlur(image_nb_120, (5, 5), 0)
cv2.imshow("Etape 8 GaussianBlur", image_gaussian_blur)
cv2.waitKey(0)
cv2.destroyWindow("Etape 8 GaussianBlur")

image_hsv = cv2.cvtColor(image_resized, cv2.COLOR_BGR2HSV)
cv2.imshow("Etape 9 HSV", image_hsv)
cv2.waitKey(0)
cv2.destroyWindow("Etape 9 HSV")

lower_red = np.array([0, 150, 150])
upper_red = np.array([10, 255, 255])
mask_red = cv2.inRange(image_hsv, lower_red, upper_red)
cv2.imshow("Etape 10 Masque rouge", mask_red)
cv2.waitKey(0)
cv2.destroyWindow("Etape 10 Masque rouge")

x_mask, y_mask = mask_red.shape
image_ligne = image_resized.copy()
points = []

for x in range(y_mask):
    ys = np.where(mask_red[:, x] > 0)[0]
    if len(ys) > 0:
        cy = int(np.mean(ys))
        points.append((x, cy))

for i in range(1, len(points)):
    cv2.line(image_ligne, points[i - 1], points[i], (255, 255, 255), 2)

cv2.imshow("Ligne", image_ligne)
cv2.waitKey(0)
cv2.destroyWindow("Ligne")

cv2.destroyAllWindows()