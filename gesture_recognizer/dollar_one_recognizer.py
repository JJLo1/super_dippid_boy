"""
The functions below have been implemented based on the pseudocode in the original paper on the 1$ recognizer:
Wobbrock, J. O., Wilson, A. D., & Li, Y. (2007, October). Gestures without libraries, toolkits or training:
a $1 recognizer for user interface prototypes. In Proceedings of the 20th annual ACM symposium on User
interface software and technology (pp. 159-168).
"""

import sys
import numpy as np
from dollar_one_utils import calc_dist_at_best_angle, calc_path_length, calc_euclidean_distance, get_bounding_box, \
    calc_centroid, rotate_by


# noinspection PyMethodMayBeStatic
class DollarOneRecognizer:

    SQUARE_SIZE = 100
    NUM_RESAMPLED_POINTS = 64

    def resample_points(self, original_points: list):
        """
        The original input points must be in the form of [(x, y), ...].
        """
        step_size = calc_path_length(original_points) / float(self.NUM_RESAMPLED_POINTS - 1)
        current_distance = 0
        new_points = [original_points[0]]  # create a new array and init with the first point

        i = 1
        while i < len(original_points):
            last_point = original_points[i-1]
            current_point = original_points[i]
            d = calc_euclidean_distance(last_point, current_point)

            if (current_distance + d) >= step_size:
                # if the distance to the next point is greater than the step size, we have to calculated
                # a new resampled point
                px = last_point[0] + ((step_size - current_distance) / d) * (current_point[0] - last_point[0])
                py = last_point[1] + ((step_size - current_distance) / d) * (current_point[1] - last_point[1])
                resampled_point = [px, py]
                new_points.append(resampled_point)

                # insert the new resampled point at the next position in the original list, so it will be the next
                # current_point!
                original_points.insert(i, resampled_point)
                current_distance = 0  # very important to reset the current position!
            else:
                # step size was not reached, just go further
                current_distance += d
            i += 1

        if len(new_points) == self.NUM_RESAMPLED_POINTS - 1:
            # for some reason the last point isn't added anymore, so to make sure we still have the specified
            # number of resampled points we add the last point in the original array at the end manually
            last_point = original_points[len(original_points)-1]
            new_points.append(last_point)

        if not len(new_points) == self.NUM_RESAMPLED_POINTS:
            sys.stderr.write(f"Len of resampled points is {len(new_points)} but should be {self.NUM_RESAMPLED_POINTS}")
            sys.exit(1)

        return new_points

    def rotate_to_zero(self, points):
        centroid = calc_centroid(points)
        first_point_x = points[0][0]
        first_point_y = points[0][1]
        rotate_angle = np.arctan2(centroid[1] - first_point_y, centroid[0] - first_point_x)

        rotated_points = rotate_by(points=points, angle=-rotate_angle)
        return rotated_points

    def scale_to_square(self, points):
        bbox = get_bounding_box(points)
        # bounding box in the form: [(min_x, min_y), (max_x, max_y)]
        bbox_width = bbox[1][0] - bbox[0][0]
        bbox_height = bbox[1][1] - bbox[0][1]

        new_points = []
        for point in points:
            p_x = point[0] * (self.SQUARE_SIZE / bbox_width)
            p_y = point[1] * (self.SQUARE_SIZE / bbox_height)
            scaled_point = [p_x, p_y]
            new_points.append(scaled_point)
        return new_points

    def translate_to_origin(self, points):
        centroid = calc_centroid(points)
        new_points = []
        for point in points:
            p_x = point[0] - centroid[0]
            p_y = point[1] - centroid[1]
            new_points.append([p_x, p_y])
        return new_points

    def normalize(self, points):
        # use all the processing functions from above to transform our set of points into the desired shape
        resampled_points = self.resample_points(points)
        rotated_points = self.rotate_to_zero(resampled_points)
        scaled_points = self.scale_to_square(rotated_points)
        translated_points = self.translate_to_origin(scaled_points)
        return translated_points

    def recognize(self, points, template_dict):
        """
        Slightly adapted from the pseudocode to work with a dictionary of templates and not just the point data.
        """
        if len(template_dict) < 1:
            print("There are no templates!")
            return

        T_new = None
        b = np.inf
        for template_name, template_data in template_dict.items():
            # we actually have a nested list as we wrapped in another list when saving to be able to replace it easily
            # so we have to unpack the templates first
            normalized_template = template_data[0]

            if len(normalized_template) != len(points):
                sys.stderr.write(f"Template {template_name} doesn't have the same size as the drawn gesture!")
                continue

            # angle values based on the original paper from Wobbrock et al.:
            dist = calc_dist_at_best_angle(points, normalized_template, -45, 45, 2)
            if dist < b:
                b = dist
                T_new = template_name

        if T_new is None:
            return
        score = 1 - b / 0.5 * np.sqrt(self.SQUARE_SIZE**2 + self.SQUARE_SIZE**2)
        return T_new, score
