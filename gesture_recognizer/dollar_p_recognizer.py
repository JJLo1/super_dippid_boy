"""
The functions below have been implemented by Michael Meckl based on the pseudocode in the paper on the $P recognizer:
Vatavu, R. D., Anthony, L., & Wobbrock, J. O. (2012, October). Gestures as point clouds: a $ P recognizer for user
interface prototypes. In Proceedings of the 14th ACM international conference on Multimodal interaction (pp. 273-280).
"""


import json
import pathlib
import sys
from typing import Optional
import numpy as np


"""
# inherit from dict to make it serializable
class Point(dict):
    def __init__(self, x, y, strokeId=None):
        dict.__init__(self, {'x': x, 'y': y, 'strokeId': strokeId})
        self.x = x
        self.y = y
        self.stroke_id = strokeId

    # def __repr__(self):
    #    return '(' + str(self.x) + ', ' + str(self.y) + '), stroke ' + str(self.stroke_id)
"""


class Point:
    def __init__(self, x, y, stroke_id=None):
        self.x = x
        self.y = y
        self.stroke_id = stroke_id


class DollarPRecognizer:

    NUM_RESAMPLED_POINTS = 32
    GESTURE_FILE_NAME = "gestures.json"

    # TODO not used at the moment because triangle and rectangle are sometimes not recognized very well so we need
    #  low numbers and there aren't many false positives, so a threshold doesn't really make sense
    THRESHOLD = 0.3  # threshold at which we reject a gesture prediction as too bad

    def __init__(self):
        self.__gesture_file_path = pathlib.Path("gesture_recognizer") / self.GESTURE_FILE_NAME
        self.existing_gestures: dict = self._load_gesture_data()

    def _load_gesture_data(self):
        # check if the file already exists
        if self.__gesture_file_path.exists():
            # if it does, load existing gestures
            with open(self.__gesture_file_path, 'r') as f:
                return json.load(f)
        else:
            sys.stderr.write(f"Gesture file '{self.GESTURE_FILE_NAME}' does not exist yet!")
            return {}

    def save_gesture(self, gesture_name, gesture_points) -> Optional[bool]:
        # normalize gesture before saving so it doesn't have to be done everytime again when trying to predict something
        # normalized_gesture = self._normalize(gesture_points)

        if self.existing_gestures.get(gesture_name):
            print(f"A gesture with the name '{gesture_name}' does already exist!")
            answer = input("Do you want to overwrite it? [y/n]\n")
            if str.lower(answer) == "y" or "yes":
                self.existing_gestures[gesture_name] = {"original": gesture_points}  # , "norm": normalized_gesture}
            else:
                print("\nSaving gesture cancelled.")
                return
        else:
            self.existing_gestures[gesture_name] = {"original": gesture_points}

        with open(self.__gesture_file_path, 'w') as f:
            json.dump(self.existing_gestures, f, indent=2)  # the indent parameter makes the file more human-readable

        return True

    def get_all_gestures(self):
        return self.existing_gestures

    def resample_points(self, original_points: list[Point], n: int):
        step_size = self.calc_path_length(original_points) / (n - 1)
        current_distance = 0
        new_points = [original_points[0]]  # create a new array and init with the first point

        i = 1
        while i < len(original_points):
            last_point = original_points[i - 1]
            current_point = original_points[i]

            if current_point.stroke_id == last_point.stroke_id:
                d = self.calc_euclidean_distance(last_point, current_point)

                if (current_distance + d) >= step_size:
                    # if the distance to the next point is greater than the step size, we have to calculated
                    # a new resampled point
                    px = last_point.x + ((step_size - current_distance) / d) * (current_point.x - last_point.x)
                    py = last_point.y + ((step_size - current_distance) / d) * (current_point.y - last_point.y)
                    resampled_point = Point(px, py)
                    resampled_point.stroke_id = current_point.stroke_id
                    new_points.append(resampled_point)

                    # insert the new resampled point at the next position in the original list, so it will be the next
                    # current_point!
                    original_points.insert(i, resampled_point)
                    current_distance = 0  # very important to reset the current position!
                else:
                    # step size was not reached, just go further
                    current_distance += d
            i += 1

        if len(new_points) == n - 1:
            # the last point isn't added anymore, so to make sure we still have the specified
            # number of resampled points we add the last point in the original array at the end manually
            last_point = original_points[len(original_points) - 1]
            new_points.append(Point(last_point.x, last_point.y, last_point.stroke_id))

        return new_points

    def scale_to_square(self, points: list[Point]):
        x_min, y_min = np.inf, np.inf
        x_max, y_max = 0, 0
        for point in points:
            x_min = min(x_min, point.x)
            y_min = min(y_min, point.y)
            x_max = max(x_max, point.x)
            y_max = max(y_max, point.y)
        scale_factor = max(x_max - x_min, y_max - y_min)

        new_points = []
        for point in points:
            p_x = (point.x - x_min) / scale_factor
            p_y = (point.y - y_min) / scale_factor
            new_points.append(Point(p_x, p_y, point.stroke_id))

        return new_points

    def translate_to_origin(self, points: list[Point], n: int):
        centroid = self.calc_centroid(points, n)

        new_points = []
        for point in points:
            p_x = point.x - centroid.x
            p_y = point.x - centroid.y
            new_points.append(Point(p_x, p_y, point.stroke_id))

        return new_points

    def calc_euclidean_distance(self, p1: Point, p2: Point):
        # Pythagorean theorem
        a = p2.x - p1.x
        b = p2.y - p1.y
        return np.sqrt(a ** 2 + b ** 2)

    def calc_path_length(self, points):
        distance = 0.0
        for i in range(1, len(points)):
            last_point = points[i - 1]
            current_point = points[i]

            if current_point.stroke_id == last_point.stroke_id:
                distance += self.calc_euclidean_distance(last_point, current_point)

        return distance

    def calc_centroid(self, points: list[Point], n):
        centroid = Point(0, 0)
        for point in points:
            centroid.x = centroid.x + point.x
            centroid.y = centroid.y + point.y

        centroid.x /= n
        centroid.y /= n
        return centroid

    def normalize(self, points: list[Point]):
        # use all the processing functions from above to transform our set of points into the desired shape
        resampled_points = self.resample_points(points, self.NUM_RESAMPLED_POINTS)
        scaled_points = self.scale_to_square(resampled_points)
        translated_points = self.translate_to_origin(scaled_points, self.NUM_RESAMPLED_POINTS)
        return translated_points

    def cloud_distance(self, points: list[Point], templates: list[Point], n: int, start: int):
        matched = [False] * n
        dist_sum = 0
        i = start

        while True:
            minimum = np.inf
            index = None
            for j, val in enumerate(matched):
                if not val:
                    dist = self.calc_euclidean_distance(points[i], templates[j])
                    if dist < minimum:
                        minimum = dist
                        index = j

            matched[index] = True
            weight = 1 - ((i - start + n) % n) / n
            dist_sum = dist_sum + weight * minimum
            i = (i + 1) % n

            if i == start:
                break

        return dist_sum

    def greedy_cloud_match(self, points: list[Point], templates: list[Point]):
        n = self.NUM_RESAMPLED_POINTS
        eps = 0.50
        step = int(n**(1 - eps))
        minimum = np.inf

        for i in range(0, n, step):  # until n because the last elem in range() is exclusive
            dist_1 = self.cloud_distance(points, templates, n, i)
            dist_2 = self.cloud_distance(templates, points, n, i)
            minimum = min(minimum, dist_1, dist_2)

        return minimum

    def predict_gesture(self, input_points):
        if len(input_points) < 2:
            sys.stderr.write("You have to draw more to predict a gesture!\n")
            return None
        if len(self.existing_gestures) < 1:
            print("There are no templates!\n")
            return None

        # normalize input points
        drawn_points = [Point(*p) for p in input_points]
        normalized_gesture = self.normalize(drawn_points)

        # try to find the correct gesture
        recognition_result = self.recognize(normalized_gesture)

        if recognition_result is not None:
            best_template, score = recognition_result
            print(f"{best_template}   (Score / Probability: {score:.3f})")
            # only change the player form if the score is good enough, if not we keep the current form
            # if score > self.THRESHOLD:
            return best_template
        else:
            print("Couldn't predict a gesture!")
        return None

    def recognize(self, points: list[Point]):
        result_template = None
        score = np.inf
        for template_name, template_data in self.existing_gestures.items():
            # quite inefficient to do this every time; SHOULD be done already when saving the template to json but
            # then the point class must be made Serializable and be converted back when reading from json file!
            template_points = template_data.get("original")
            drawn_template_points = [Point(*p) for p in template_points]  # TODO stroke_id not used in templates
            normalized_template = self.normalize(drawn_template_points)

            dist = self.greedy_cloud_match(points, normalized_template)
            if score > dist:
                score = dist
                result_template = template_name

        # additional score function was taken from https://github.com/sonovice/dollarpy
        score = max((2 - score) / 2, 0)
        if result_template is None or score == 0:
            return

        return result_template, score
