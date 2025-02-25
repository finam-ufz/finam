import datetime as dt
import unittest

import finam as fm


class TestInspect(unittest.TestCase):
    def test_slot(self):
        inp = fm.Input(
            name="In", static=True, time=None, grid=fm.UniformGrid((15, 10)), units="m"
        )
        _s1 = fm.tools.inspect(inp)

    def test_adapter(self):
        ada = fm.adapters.ValueToGrid(grid=fm.UniformGrid((20, 15)))
        _s1 = fm.tools.inspect(ada)

    def test_inspect_component(self):
        comp1 = fm.components.WeightedSum(inputs=["A", "B", "C"])
        comp2 = fm.components.TimeTrigger(
            in_info=fm.Info(time=None, grid=None),
            start=dt.datetime(2000, 1, 1),
            step=dt.timedelta(days=1),
        )

        comp1.initialize()
        comp2.initialize()

        _s1 = fm.tools.inspect(comp1)
        _s2 = fm.tools.inspect(comp2)


if __name__ == "__main__":
    unittest.main()
