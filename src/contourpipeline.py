import cv2
import numpy
import math
from enum import Enum


class ContourPipeline:
    """
    An OpenCV pipeline generated by GRIP.
    """

    def __init__(self):
        """initializes all values to presets or None if need to be set
        """

        self.__blur_0_type = BlurType.Box_Blur
        self.__blur_0_radius = 2.7027027027027026

        self.blur_0_output = None

        self.__cv_canny_image = self.blur_0_output
        self.__cv_canny_threshold1 = 100.0
        self.__cv_canny_threshold2 = 150.0
        self.__cv_canny_aperturesize = 3.0
        self.__cv_canny_l2gradient = False

        self.cv_canny_output = None

        self.__blur_1_input = self.cv_canny_output
        self.__blur_1_type = BlurType.Box_Blur
        self.__blur_1_radius = 17.882032976372596

        self.blur_1_output = None

        self.__find_contours_input = self.blur_1_output
        self.__find_contours_external_only = False

        self.find_contours_output = None

        self.__filter_contours_contours = self.find_contours_output
        self.__filter_contours_min_area = 1000.0
        self.__filter_contours_min_perimeter = 0
        self.__filter_contours_min_width = 0
        self.__filter_contours_max_width = 500.0
        self.__filter_contours_min_height = 0
        self.__filter_contours_max_height = 1000
        self.__filter_contours_solidity = [0.0, 100]
        self.__filter_contours_max_vertices = 1000000
        self.__filter_contours_min_vertices = 0
        self.__filter_contours_min_ratio = 0
        self.__filter_contours_max_ratio = 1000

        self.filter_contours_output = None


    def process(self, source0):
        """
        Runs the pipeline and sets all outputs to new values.
        """
        # Step Blur0:
        self.__blur_0_input = source0
        (self.blur_0_output) = self.__blur(self.__blur_0_input, self.__blur_0_type, self.__blur_0_radius)

        # Step CV_Canny0:
        self.__cv_canny_image = self.blur_0_output
        (self.cv_canny_output) = self.__cv_canny(self.__cv_canny_image, self.__cv_canny_threshold1, self.__cv_canny_threshold2, self.__cv_canny_aperturesize, self.__cv_canny_l2gradient)

        # Step Blur1:
        self.__blur_1_input = self.cv_canny_output
        (self.blur_1_output) = self.__blur(self.__blur_1_input, self.__blur_1_type, self.__blur_1_radius)

        # Step Find_Contours0:
        self.__find_contours_input = self.blur_1_output
        (self.find_contours_output) = self.__find_contours(self.__find_contours_input, self.__find_contours_external_only)

        # Step Filter_Contours0:
        self.__filter_contours_contours = self.find_contours_output
        (self.filter_contours_output) = self.__filter_contours(self.__filter_contours_contours, self.__filter_contours_min_area, self.__filter_contours_min_perimeter, self.__filter_contours_min_width, self.__filter_contours_max_width, self.__filter_contours_min_height, self.__filter_contours_max_height, self.__filter_contours_solidity, self.__filter_contours_max_vertices, self.__filter_contours_min_vertices, self.__filter_contours_min_ratio, self.__filter_contours_max_ratio)

        return self.filter_contours_output

    @staticmethod
    def __cv_canny(image, thres1, thres2, aperture_size, gradient):
        """Applies a canny edge detection to the image.
        Args:
           image: A numpy.ndarray as the input.
           thres1: First threshold for the canny algorithm. (number)
           thres2: Second threshold for the canny algorithm. (number)
           aperture_size: Aperture size for the canny operation. (number)
           gradient: If the L2 norm should be used. (boolean)
        Returns:
            The edges as a numpy.ndarray.
        """
        return cv2.Canny(image, thres1, thres2, apertureSize=(int)(aperture_size),
            L2gradient=gradient)

    @staticmethod
    def __blur(src, type, radius):
        """Softens an image using one of several filters.
        Args:
            src: The source mat (numpy.ndarray).
            type: The blurType to perform represented as an int.
            radius: The radius for the blur as a float.
        Returns:
            A numpy.ndarray that has been blurred.
        """
        if(type is BlurType.Box_Blur):
            ksize = int(2 * round(radius) + 1)
            return cv2.blur(src, (ksize, ksize))
        elif(type is BlurType.Gaussian_Blur):
            ksize = int(6 * round(radius) + 1)
            return cv2.GaussianBlur(src, (ksize, ksize), round(radius))
        elif(type is BlurType.Median_Filter):
            ksize = int(2 * round(radius) + 1)
            return cv2.medianBlur(src, ksize)
        else:
            return cv2.bilateralFilter(src, -1, round(radius), round(radius))

    @staticmethod
    def __find_contours(input, external_only):
        """Sets the values of pixels in a binary image to their distance to the nearest black pixel.
        Args:
            input: A numpy.ndarray.
            external_only: A boolean. If true only external contours are found.
        Return:
            A list of numpy.ndarray where each one represents a contour.
        """
        if(external_only):
            mode = cv2.RETR_EXTERNAL
        else:
            mode = cv2.RETR_LIST
        method = cv2.CHAIN_APPROX_SIMPLE
        contours, hierarchy =cv2.findContours(input, mode=mode, method=method)
        return contours

    @staticmethod
    def __filter_contours(input_contours, min_area, min_perimeter, min_width, max_width,
                        min_height, max_height, solidity, max_vertex_count, min_vertex_count,
                        min_ratio, max_ratio):
        """Filters out contours that do not meet certain criteria.
        Args:
            input_contours: Contours as a list of numpy.ndarray.
            min_area: The minimum area of a contour that will be kept.
            min_perimeter: The minimum perimeter of a contour that will be kept.
            min_width: Minimum width of a contour.
            max_width: MaxWidth maximum width.
            min_height: Minimum height.
            max_height: Maximimum height.
            solidity: The minimum and maximum solidity of a contour.
            min_vertex_count: Minimum vertex Count of the contours.
            max_vertex_count: Maximum vertex Count.
            min_ratio: Minimum ratio of width to height.
            max_ratio: Maximum ratio of width to height.
        Returns:
            Contours as a list of numpy.ndarray.
        """
        output = []
        for contour in input_contours:
            x,y,w,h = cv2.boundingRect(contour)
            if (w < min_width or w > max_width):
                continue
            if (h < min_height or h > max_height):
                continue
            area = cv2.contourArea(contour)
            if (area < min_area):
                continue
            if (cv2.arcLength(contour, True) < min_perimeter):
                continue
            hull = cv2.convexHull(contour)
            solid = 100 * area / cv2.contourArea(hull)
            if (solid < solidity[0] or solid > solidity[1]):
                continue
            if (len(contour) < min_vertex_count or len(contour) > max_vertex_count):
                continue
            ratio = (float)(w) / h
            if (ratio < min_ratio or ratio > max_ratio):
                continue
            output.append(contour)
        return output


BlurType = Enum('BlurType', 'Box_Blur Gaussian_Blur Median_Filter Bilateral_Filter')

