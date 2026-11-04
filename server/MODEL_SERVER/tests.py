import unittest
from unittest import mock

import numpy as np

import predictor


class FakeModel:
    def __init__(self):
        self.sizes = []

    def __call__(self, batch, training):
        self.sizes.append(len(batch))
        return mock.Mock(numpy=lambda: batch[:, :1, 0, 0])


class PredictSpotsTests(unittest.TestCase):
    def setUp(self):
        self.model = FakeModel()
        patcher = mock.patch.object(predictor, "get_model", return_value=self.model)
        patcher.start()
        self.addCleanup(patcher.stop)

    def crops(self, values):
        crops = np.zeros((len(values), 4, 4, 3), dtype=np.uint8)
        crops[:, 0, 0, 2] = values
        return crops

    def test_large_requests_are_split_into_bounded_batches(self):
        values = [255 if i % 3 == 0 else 0 for i in range(150)]
        statuses = predictor.predict_spots(self.crops(values))
        self.assertEqual(self.model.sizes, [64, 64, 22])
        self.assertEqual(statuses, ["occupied" if v else "empty" for v in values])

    def test_empty_request_never_calls_the_model(self):
        self.assertEqual(predictor.predict_spots(self.crops([])), [])
        self.assertEqual(self.model.sizes, [])


if __name__ == "__main__":
    unittest.main()
