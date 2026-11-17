"""Validate a native point-to-center boundary observation."""
import math


def _vector(values, dimension=None):
    if not isinstance(values, (list, tuple)) or not values:
        raise ValueError("Expected nonempty coordinate")
    if dimension is not None and len(values) != dimension:
        raise ValueError("Coordinate dimension differs")
    if any(isinstance(x, bool) or not isinstance(x, (int, float))
           or not math.isfinite(x) for x in values):
        raise ValueError("Nonfinite or invalid coordinate")
    return [float(x) for x in values]


def boundary_observation(point, centers, assignment, distance_row=None):
    """Check the native cdist row, then report its two smallest distances."""
    point = _vector(point)
    if not isinstance(centers, (list, tuple)) or len(centers) < 2:
        raise ValueError("At least two centers required")
    centers = [_vector(center, len(point)) for center in centers]
    if type(assignment) is not int or not 0 <= assignment < len(centers):
        raise ValueError("Invalid recorded assignment")
    if distance_row is None:
        raise ValueError("Native cdist row required")
    distances = _vector(distance_row, len(centers))
    geometric = [math.dist(point, center) for center in centers]
    for measured, expected, center in zip(distances, geometric, centers):
        # CUDA cdist may use float32 matrix multiplication; cancellation in
        # squared distances grows with the coordinate magnitudes.
        scale = max(1.0, sum(x * x for x in point) + sum(x * x for x in center))
        if abs(measured * measured - expected * expected) > 5e-6 * scale:
            raise ValueError("Native distance contradicts coordinates")
    nearest = sorted(range(len(centers)), key=lambda i: (distances[i], i))[:2]
    if assignment != nearest[0]:
        raise ValueError("Recorded assignment contradicts native distances")
    first, second = nearest
    return {
        "point_coordinate": point,
        "nearest_center_id": first,
        "nearest_distance": distances[first],
        "second_center_id": second,
        "second_distance": distances[second],
        "distance_margin": distances[second] - distances[first],
        "recorded_assignment": assignment,
    }
