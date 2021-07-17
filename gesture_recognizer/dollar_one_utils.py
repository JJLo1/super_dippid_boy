"""
All functions below, unless otherwise noted, have been implemented based on the pseudocode in the original paper on the
1$ recognizer:
Wobbrock, J. O., Wilson, A. D., & Li, Y. (2007, October). Gestures without libraries, toolkits or training:
a $1 recognizer for user interface prototypes. In Proceedings of the 20th annual ACM symposium on User
interface software and technology (pp. 159-168).
"""

import sys
import numpy as np


def degree_to_radians(degree):
    return degree * np.pi / 180.0


def calc_euclidean_distance(p1, p2):
    # Pythagorean theorem
    a = p2[0] - p1[0]
    b = p2[1] - p1[1]
    return np.sqrt(a**2 + b**2)
    # alternatively: return np.linalg.norm(p1 - p2)


def calc_path_length(points):
    distance = 0.0
    for i in range(1, len(points)):
        last_point = points[i-1]
        current_point = points[i]
        distance += calc_euclidean_distance(last_point, current_point)

    return distance


def calc_path_distance(A, B):
    if len(A) != len(B):
        print("Error! Samples A and B are not equal in length!")
        sys.exit(1)

    distance = 0
    for i in range(1, len(A)):
        distance += calc_euclidean_distance(A[i], B[i])

    return distance / len(A)


def calc_centroid(points: np.ndarray):
    """
    Function taken from the provided "Computational Geometry for Gesture Recognition" notebook.
    """
    xs, ys = zip(*points)
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def rotate_by(points, angle):
    centroid = calc_centroid(points)
    rotated_points = []
    for point in points:
        # calculate the distance of this point to the centroid of all points
        centroid_dist_x = point[0] - centroid[0]
        centroid_dist_y = point[1] - centroid[1]

        p_x = centroid_dist_x * np.cos(angle) - centroid_dist_y * np.sin(angle) + centroid[0]
        p_y = centroid_dist_x * np.sin(angle) + centroid_dist_y * np.cos(angle) + centroid[1]
        rotated_point = [p_x, p_y]
        rotated_points.append(rotated_point)

    return rotated_points


def get_bounding_box(points):
    # get min and max values along the first axis (i.e. column-wise) as we only have to columns (x and y)
    min_point = np.min(points, axis=0)
    max_point = np.max(points, axis=0)
    return [(min_point[0], min_point[1]), (max_point[0], max_point[1])]


def calc_dist_at_angle(points, template, angle):
    new_points = rotate_by(points, angle)
    distance = calc_path_distance(new_points, template)
    return distance


def calc_dist_at_best_angle(points, template, angle_a, angle_b, angle_delta):
    phi = 0.5 * (-1 + np.sqrt(5))  # value for phi taken from the paper

    x1 = phi * angle_a + (1 - phi) * angle_b
    x2 = (1 - phi) * angle_a + phi * angle_b
    f1 = calc_dist_at_angle(points, template, x1)
    f2 = calc_dist_at_angle(points, template, x2)

    while np.abs(angle_b - angle_a) > angle_delta:
        if f1 < f2:
            angle_b = x2
            x2 = x1
            f2 = f1
            x1 = phi * angle_a + (1 - phi) * angle_b
            f1 = calc_dist_at_angle(points, template, x1)
        else:
            angle_a = x1
            x1 = x2
            f1 = f2
            x2 = (1 - phi) * angle_a + phi * angle_b
            f2 = calc_dist_at_angle(points, template, x2)

    return min(f1, f2)
