import unittest


class TestBase(unittest.TestCase):
    def assertResultRepresentation(self, expected_result, actual_result):
        self.assertEqual(actual_result.__repr__(), expected_result.__repr__())

    def assertResultRepresentations(self, expected_results, actual_results):
        self.assertEqual(
            len(expected_results),
            len(actual_results),
            "Expected results and actual results are not equal",
        )
        for idx, actual_result in enumerate(actual_results):
            self.assertResultRepresentation(actual_result, expected_results[idx])
