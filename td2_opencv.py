import cv2
import numpy as np

image2 = cv2.imread("image2.png")
if image2 is None:
    print("Erreur : Impossible de charger 'image2.png'. Passez directement au temps réel.")
else:
    image2_gris = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
    image2_blur = cv2.GaussianBlur(image2_gris, (5, 5), 0)
    
    cv2.imshow("Image filtree (GaussianBlur)", image2_blur)
    cv2.waitKey(0)

    sommets = cv2.goodFeaturesToTrack(image2_blur, 10, qualityLevel=0.1, minDistance=10)
    
    if sommets is not None:
        sommets = np.int32(sommets)

        coordonnees = []
        for i, s in enumerate(sommets):
            x, y = s.ravel()
            coordonnees.append((x, y))
            print(f"Sommet {i + 1} : x = {x}, y = {y}")

        coordonnees = np.array(coordonnees)

        image2_sommets = image2.copy()
        for (x, y) in coordonnees:
            cv2.circle(image2_sommets, (x, y), 5, (0, 255, 0), -1)

        cv2.imshow("Sommets detectes", image2_sommets)
        cv2.waitKey(0)

        x_max_index = np.argmax(coordonnees[:, 0])
        x_min_index = np.argmin(coordonnees[:, 0])

        sommet_xmax = coordonnees[x_max_index]
        sommet_xmin = coordonnees[x_min_index]

        print("Sommet avec x maximum :", sommet_xmax)
        print("Sommet avec x minimum :", sommet_xmin)

        x_moyenne = int((sommet_xmax[0] + sommet_xmin[0]) / 2)

        image2_ligne = image2_sommets.copy()
        cv2.line(image2_ligne, (x_moyenne, 0), (x_moyenne, image2.shape[0]), (0, 0, 255), 2)

        cv2.imshow("Ligne centrale (Xmoyenne)", image2_ligne)
        cv2.waitKey(0)


        nb_gauche = np.sum(coordonnees[:, 0] < x_moyenne)
        nb_droite = np.sum(coordonnees[:, 0] > x_moyenne)

        print("Nombre de sommets a gauche de la ligne :", nb_gauche)
        print("Nombre de sommets a droite de la ligne :", nb_droite)

    cv2.destroyAllWindows()

def traitement_temps_reel():
    vidcap = cv2.VideoCapture(0)

    if not vidcap.isOpened():
        print("Impossible d'ouvrir la caméra")
        return

    print("Appuyez sur 'q' pour quitter le flux vidéo.")

    while True:
        ret, frame = vidcap.read()
        if not ret:
            print("Erreur de lecture du flux vidéo")
            break

        frame_gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_blur = cv2.GaussianBlur(frame_gris, (5, 5), 0)

        sommets = cv2.goodFeaturesToTrack(frame_blur, 10, qualityLevel=0.1, minDistance=10)

        if sommets is not None:
            coords = np.int32(sommets).reshape(-1, 2)

            for (x, y) in coords:
                cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

            x_max = coords[:, 0].max()
            x_min = coords[:, 0].min()
            x_moy = int((x_max + x_min) / 2)
            
            cv2.line(frame, (x_moy, 0), (x_moy, frame.shape[0]), (0, 0, 255), 2)

            nb_g = np.sum(coords[:, 0] < x_moy)
            nb_d = np.sum(coords[:, 0] > x_moy)
            
            cv2.putText(frame, f"Gauche: {nb_g}  Droite: {nb_d}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

        cv2.imshow("Flux video temps reel", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    vidcap.release()
    cv2.destroyAllWindows()

traitement_temps_reel()