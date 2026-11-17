import unittest

import calculater


class CalculatorVoiceTests(unittest.TestCase):
    def test_google_x_transcription_maps_to_multiplication(self):
        expression = calculater.spoken_to_expression("6 x 4")
        self.assertEqual(expression, "6 * 4")
        self.assertEqual(calculater.evaluate_node(calculater.parse_expression(expression)), 24)

    def test_spoken_scientific_operation(self):
        expression = calculater.spoken_to_expression("square root of eighty one")
        self.assertEqual(expression, "sqrt(81)")
        self.assertEqual(calculater.evaluate_node(calculater.parse_expression(expression)), 9)

    def test_rejects_multiple_or_unrelated_operations(self):
        for phrase in ("two plus three times four", "hello two plus three"):
            with self.subTest(phrase=phrase):
                with self.assertRaises(ValueError):
                    calculater.spoken_to_expression(phrase)


if __name__ == "__main__":
    unittest.main()
