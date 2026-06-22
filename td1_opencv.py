import cv2
import numpy as np
image = cv2.imread("image1.png")

cv2.imshow("Image originale", image)
cv2.waitKey(0)
cv2.destroyWindow("Image originale")

height, width, channels = image.shape
print("Largeur (axe X) :", width)
print("Hauteur (axe Y) :", height)

image_resized = cv2.resize(image, (800, 600))
cv2.imwrite("image1_resized.png", image_resized)

cv2.imshow("Image redimensionnee", image_resized)
cv2.waitKey(0)
cv2.destroyWindow("Image redimensionnee")

image_gris = cv2.cvtColor(image_resized, cv2.COLOR_BGR2GRAY)

cv2.imshow("Image en niveaux de gris", image_gris)
cv2.waitKey(0)
cv2.destroyWindow("Image en niveaux de gris")

(_, image_nb_120) = cv2.threshold(image_gris, 120, 255, cv2.THRESH_BINARY)
cv2.imshow("Noir et blanc - seuil 120", image_nb_120)
cv2.waitKey(0)
cv2.destroyWindow("Noir et blanc - seuil 120")

(_, image_nb_70) = cv2.threshold(image_gris, 70, 255, cv2.THRESH_BINARY)
cv2.imshow("Noir et blanc - seuil 70", image_nb_70)
cv2.waitKey(0)
cv2.destroyWindow("Noir et blanc - seuil 70")

for seuil in [50, 100, 150, 200]:
    (_, img_var) = cv2.threshold(image_gris, seuil, 255, cv2.THRESH_BINARY)
    cv2.imshow(f"Seuil = {seuil}", img_var)
    cv2.waitKey(0)
    cv2.destroyWindow(f"Seuil = {seuil}")
image_blur = cv2.blur(image_nb_120, (5, 5))
cv2.imshow("Filtre Blur", image_blur)
cv2.waitKey(0)
cv2.destroyWindow("Filtre Blur")

image_median_blur = cv2.medianBlur(image_nb_120, 5)
cv2.imshow("Filtre medianBlur", image_median_blur)
cv2.waitKey(0)
cv2.destroyWindow("Filtre medianBlur")

image_gaussian_blur = cv2.GaussianBlur(image_nb_120, (5, 5), 0)
cv2.imshow("Filtre GaussianBlur", image_gaussian_blur)
cv2.waitKey(0)
cv2.destroyWindow("Filtre GaussianBlur")
image_hsv = cv2.cvtColor(image_resized, cv2.COLOR_BGR2HSV)
cv2.imshow("Image HSV", image_hsv)
cv2.waitKey(0)
cv2.destroyWindow("Image HSV")
cv2.imshow("Masque rouge", mask_red)
cv2.waitKey(0)
cv2.destroyWindow("Masque rouge")

h_mask, w_mask = mask_red.shape

image_ligne = image_resized.copy()
points = []

for x in range(w_mask):
    ys = np.where(mask_red[:, x] > 0)[0]
    if len(ys) > 0:
        cy = int(np.mean(ys))
        points.append((x, cy))

for i in range(1, len(points)):
    cv2.line(image_ligne, points[i - 1], points[i], (0, 255, 0), 2)

cv2.imshow("Ligne centrale de la surface rouge", image_ligne)
cv2.waitKey(0)
cv2.destroyWindow("Ligne centrale de la surface rouge")

cv2.destroyAllWindows()