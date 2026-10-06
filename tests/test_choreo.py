"""Choreography layer (scripts/choreo.py): cue validation and the default level sequence."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import choreo
from choreo import ChoreoError, cue, levels, validate


class ChoreoTests(unittest.TestCase):
    def test_rejects_bad_cues(self):
        with self.assertRaises(ChoreoError): cue('e0', 'colour', 0, .3, 0, 1)        # unknown property
        with self.assertRaises(ChoreoError): cue('e0', 'level', 0, .05, 0, 1)        # too short: a snap
        with self.assertRaises(ChoreoError): cue('e0', 'level', 0, 2.0, 0, 1)        # too slow for a state
        with self.assertRaises(ChoreoError): cue('e0', 'level', 0, .3, 0, 1, 'bounce')
        with self.assertRaises(ChoreoError): validate([cue('e0', 'level', 0, .3, 0, 1), cue('e0', 'level', .1, .3, 1, 2)], 5)   # overlap
        with self.assertRaises(ChoreoError): validate([cue('e0', 'level', 0, .3, 0, 1), cue('e0', 'level', 1, .3, 2, 1)], 5)   # discontinuous
        with self.assertRaises(ChoreoError): validate([cue('e0', 'level', 4.9, .3, 0, 1)], 5)   # final scene not settled

    def test_levels_fall_first_then_rise_overlapping(self):
        c = levels('e0', 'level', [2, 1, 1, 0], [0, 1, 2, 3])
        self.assertEqual([x[5:] for x in c], [[0, 2], [2, 1], [1, 0]])
        rise, fall = c[0], c[1]
        self.assertAlmostEqual(rise[2], choreo.EXIT * choreo.OVERLAP)   # a rise waits for 80% of a fall
        self.assertEqual((rise[4], fall[4]), ('out', 'in'))
        self.assertEqual(fall[2], 1)                                  # a fall starts on its event
        validate(c, 3.5)

    def test_emphasis_pulses_repeat(self):
        validate([cue('n:a', 'pop', 0, .4, 0, 1, 'linear'), cue('n:a', 'pop', 1, .4, 0, 1, 'linear')], 2)


if __name__ == '__main__':
    unittest.main()
