#!/usr/bin/env python3
import numpy as np
import cv2

def thermal_mapping (t_img, n_img, temp_tol = 5, show=False,
                     conv_gray=False, inv_therm=False):
    if conv_gray: n_img = cv2.cvtColor(n_img, cv2.COLOR_BGR2GRAY)
    if inv_therm: t_img = t_img[:][::-1]

    t_img = get_mask(t_img)

def crop_image(img, x_range=(0,-1), y_range=(0,-1)):
    img = img.tolist()
    img = [i[x_range[0]:x_range[1]] for i in img[y_range[0]:y_range[1]]]
    img = np.array(img).astype(np.uint8)
    return img

def get_mask(img, val=255, range=15, conv_gray=False):
    if conv_gray: img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = img.tolist()
    masker = lambda x : 0 if abs(x-val)<=range else 255
    mask = [[masker(pixel) for pixel in line] for line in img]
    return np.array(mask).astype(np.uint8)

def get_sunspot_blobs(img):
    g_kernel = cv2.getGaborKernel((21, 21),  # kernel size
                                  8.0,  # sigma - std deviation of gaussian function
                                  np.pi/6,  # theta - orientation of the normal to the parallel stripes
                                  10.0,  # lambda - wavelength of the sunusoidal factor
                                  0.5,  # gamma - spatial aspect ratio
                                  10,  # psi - phase offset
                                  ktype=cv2.CV_64F)  # ktype - type and range of values that each pixel in the gabor kernel can hold
    #img = cv2.imread('../mem/pics/sample.jpeg')
    #img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    f_img = cv2.filter2D(img, cv2.CV_8UC3, g_kernel)

    (thresh, img) = cv2.threshold(f_img, 230, 255, cv2.THRESH_BINARY)
    img = cv2.bitwise_not(img)
    kernel = np.ones((7,7),np.uint8)
    img = cv2.dilate(img,kernel,iterations = 3)
    #masked = cv2.bitwise_and(img, img, mask=img)
    return img

def get_shadow_blobs(img, mask):
    g_kernel = cv2.getGaborKernel((21, 21),  # kernel size
                                  8.0,  # sigma - std deviation of gaussian function
                                  np.pi/6,  # theta - orientation of the normal to the parallel stripes
                                  10.0,  # lambda - wavelength of the sunusoidal factor
                                  0.5,  # gamma - spatial aspect ratio
                                  10,  # psi - phase offset
                                  ktype=cv2.CV_64F)  # ktype - type and range of values that each pixel in the gabor kernel can hold
    #img = cv2.imread('../mem/pics/sample.jpeg')
    #img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    f_img = cv2.filter2D(img, cv2.CV_8UC3, g_kernel)

    (thresh, img) = cv2.threshold(f_img, 230, 255, cv2.THRESH_BINARY)
    img = cv2.bitwise_not(img)
    kernel = np.ones((7,7),np.uint8)
    img = cv2.dilate(img,kernel,iterations = 3)
    shadow = cv2.bitwise_not(img)+mask

    #masked = cv2.bitwise_and(img, img, mask=img)
    return shadow

def get_centroids(img, max_only=True):
    from polylabel import polylabel
    contours, dont_care = cv2.findContours(img,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    l = [cv2.moments(c) for c in contours]
    if len(l) == 0:
        return [[320, 120]]
    if max_only:
        l = [c['m00'] for c in l]
        i = l.index(max(l))
        biggest_contour = contours[i]
        print(biggest_contour)
        return [polylabel([[vertice[0] for vertice in biggest_contour]])]
    else:
        centroids = []
        for c in contours:
            centroids.append(polylabel([[vertice[0] for vertice in c]]))
        return centroids

def draw_centroids(img,centroids,contours=None):
    if contours is not None:
        if len(contours)>0:
            img = cv2.drawContours(img, contours,-1, (0,255,0), 3)
    for cX, cY in centroids:
        cX, cY = int(cX), int(cY)
        #img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        cv2.circle(img, (cX, cY), 5, (255,0,0), -1)
        cv2.putText(img, "centroid", (cX - 25, cY - 25),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        #img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img
    ################################################################################
    # if show:
    #     cv2.imshow('image', img)
    #     cv2.imshow('filtered image', img)
    #     cv2.imshow('masked', masked)
    #     h, w = g_kernel.shape[:2]
    #     g_kernel = cv2.resize(f_img, (3*w, 3*h), interpolation=cv2.INTER_CUBIC)
    #     #cv2.imshow('gabor kernel (resized)', g_kernel)
    #     cv2.waitKey(0)
    #     cv2.destroyAllWindows()

def get_dir_sunlight(n_img, t_img):
    masked = np.array([[0]*240]*160+n_img[160:].tolist()).astype(np.uint8)
    blobs = cv2.bitwise_not(get_sunspot_blobs(masked))
    return get_centroids(blobs, True)

def get_dir_shadow(n_img, t_img):
    masked = np.array([[0]*240]*160+n_img[160:].tolist()).astype(np.uint8)
    blobs = cv2.bitwise_not(get_shadow_blobs(n_img, mask))
    return get_centroids(blobs, True)

def get_brightest_pixel(n_img, t_img):
    lista = n_img
    c1 = 160
    maximum = -float("inf")
    maximum_pos = [160,0]
    while c1<319:
        for j in range(240):
            if lista[c1][j] >= maximum:
                maximum = lista[c1][j]
                maximum_pos = [j,c1] 
        c1+=1
    return [maximum_pos]

def get_darkest_pixel(n_img, t_img):
    lista = n_img
    c1 = 160
    maximum = float("inf")
    maximum_pos = [160,0]
    while c1<319:
        for j in range(240):
            if lista[c1][j]<maximum:
                maximum = lista[c1][j]
                maximum_pos = [j,c1] 
        c1+=1
    return [maximum_pos]


# path_b = "/home/antonio/Downloads/pics/BW/"
# path_t = path_BW = "/home/antonio/Downloads/pics/Thermal/"

# for img_n in os.listdir(path_b):
#     try:
#         img = cv2.imread(path_t+img_n[:-5]+"T.jpg")
#         original = cv2.imread(path_b+img_n)
#         objective = get_dir_shadow(original,img)
#         dir = draw_centroids(original, objective)
#         cv2.imshow('Shadow', dir)
#         objective = get_dir_sunlight(original,img)
#         dir = draw_centroids(original, objective)
#         cv2.imshow('Sunlight', dir)
#         cv2.waitKey(0)
#         cv2.destroyAllWindows()
#     except:
#         pass
