import unittest

import finam as fm


def u(s):
    return str(fm.UNITS.Unit(s))


class TestCfUnits(unittest.TestCase):
    def test_cf_units(self):
        self.assertEqual(u("mm"), "mm")
        self.assertEqual(u("millimeter"), "mm")
        self.assertEqual(u("kilometer"), "km")

        self.assertEqual(u("meter ** 2"), "m2")
        self.assertEqual(u("1 / meter"), "m-1")

        self.assertEqual(u("degree_north"), "degrees_north")
        self.assertEqual(u("degree_east"), "degrees_east")

        self.assertEqual(u("°C"), "°C")
        self.assertEqual(u("degC"), "°C")
        self.assertEqual(u("degree_Celsius"), "°C")

        # "dimensionless" representation inconsistent across different pint versions
        # will be "1" for newer versions (>=0.24.1) to be in line with cf-conventions
        self.assertTrue(u("") in ("1", "dimensionless", ""))
        self.assertTrue(u("1") in ("1", "dimensionless", ""))
        self.assertTrue(u("m/m") in ("1", "dimensionless", ""))

        self.assertEqual(u("m/s"), "m s-1")
        self.assertEqual(u("m s-1"), "m s-1")


if __name__ == "__main__":
    unittest.main()
