"""Basic tests for the header quality pipeline.

Run with either
    python -m unittest discover tests -v
    python -m pytest tests            (if pytest is installed)

Tests marked "real data" run only after the dataset has been built
(data/processed/*.csv.gz) and skip themselves otherwise.
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import build_dataset  # noqa: E402
import check_site_sync  # noqa: E402
import geometry  # noqa: E402
import mixed_model  # noqa: E402
import modeling  # noqa: E402
import models_attack  # noqa: E402
import models_defense  # noqa: E402
import rankings  # noqa: E402

PROC = ROOT / "data" / "processed"
HAVE_DATA = (PROC / "headed_shots.csv.gz").exists() and (PROC / "aerial_duels.csv.gz").exists()
HAVE_PRED = (PROC / "duel_predictions.csv.gz").exists()


class TestGeometry(unittest.TestCase):
    def test_distance_and_angle(self):
        self.assertAlmostEqual(float(geometry.dist_to_goal(108, 40)), 12.0)
        # from the middle of the goal line the mouth opens to 180 degrees
        self.assertAlmostEqual(float(geometry.goal_angle(119.999, 40)), 180, places=1)
        # further out and wider means a smaller angle
        self.assertGreater(geometry.goal_angle(110, 40), geometry.goal_angle(100, 40))
        self.assertGreater(geometry.goal_angle(110, 40), geometry.goal_angle(110, 20))

    def test_boxes(self):
        self.assertTrue(geometry.in_box(110, 40))
        self.assertFalse(geometry.in_box(100, 40))
        self.assertTrue(geometry.in_six(116, 40))
        self.assertTrue(geometry.in_own_box(5, 40))

    def test_triangle(self):
        a, b, c = np.array([0, 0]), np.array([10, 0]), np.array([0, 10])
        self.assertTrue(geometry.point_in_triangle(np.array([2, 2]), a, b, c))
        self.assertFalse(geometry.point_in_triangle(np.array([8, 8]), a, b, c))


def _event(i, t, typ, team=1, related=None, extra=None):
    e = {"id": f"e{i}", "period": 1, "timestamp": f"00:00:{t:06.3f}", "type": {"name": typ},
         "team": {"id": team}, "related_events": related or []}
    e.update(extra or {})
    return e


class TestEventLogic(unittest.TestCase):
    def test_duel_delivery_skips_linked_events(self):
        """The winner's own header can be logged before the duel. It must not be
        picked as the incoming delivery, or the model would see the outcome."""
        cross = _event(0, 10.0, "Pass", team=1)
        winners_header = _event(1, 11.0, "Pass", team=2)
        duel = _event(2, 11.1, "Duel", team=1, related=["e1"])
        events = [cross, winners_header, duel]
        self.assertEqual(build_dataset.last_pass_before(events, 2)["id"], "e0")

    def test_delivery_window(self):
        old = _event(0, 1.0, "Pass")
        later = _event(1, 9.0, "Duel")
        self.assertIsNone(build_dataset.last_pass_before([old, later], 1))


class TestNoLeakage(unittest.TestCase):
    OUTCOME_COLUMNS = {"goal", "on_target", "outcome", "sb_xg", "end_x", "end_y", "def_won", "next_team_won",
                       "next_x", "next_y", "next_type", "opp_shot_10s", "opp_xg_10s", "opp_goal_10s", "action"}

    def test_attack_features_exclude_outcomes(self):
        feats = set(models_attack.NUM + models_attack.BOOL + models_attack.CAT)
        self.assertFalse(feats & self.OUTCOME_COLUMNS, feats & self.OUTCOME_COLUMNS)
        self.assertNotIn("under_pressure", feats)

    def test_defense_features_exclude_outcomes(self):
        for feats in (models_defense.DUEL_NUM + models_defense.DUEL_CAT,
                      models_defense.CLEAR_NUM + models_defense.CLEAR_CAT):
            self.assertFalse(set(feats) & self.OUTCOME_COLUMNS, set(feats) & self.OUTCOME_COLUMNS)

    def test_main_models_use_height_only(self):
        df = pd.DataFrame({"height_cm": [180.0, 190.0], "ea_jumping": [70.0, 80.0], "weight_kg": [75.0, 80.0]})
        self.assertEqual(modeling.physical_columns(df), ["height_cm"])


class TestFolds(unittest.TestCase):
    def test_no_match_in_train_and_test_synthetic(self):
        groups = np.repeat(np.arange(200), 7)
        for tr, te in modeling.match_folds(groups, 5):
            self.assertFalse(set(groups[tr]) & set(groups[te]))
            self.assertEqual(len(tr) + len(te), len(groups))

    @unittest.skipUnless(HAVE_DATA, "real data not built")
    def test_no_match_in_train_and_test_real(self):
        d = models_defense.prepare_duels()
        g = d["match_id"].values
        seen = np.zeros(len(g), int)
        for tr, te in modeling.match_folds(g, 5):
            self.assertFalse(set(g[tr]) & set(g[te]))
            seen[te] += 1
        self.assertTrue((seen == 1).all(), "every row is tested exactly once")


@unittest.skipUnless(HAVE_DATA, "real data not built")
class TestRealData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shots = models_attack.prepare()
        cls.duels = models_defense.prepare_duels()

    def test_keys_and_targets_complete(self):
        for df, cols in ((self.shots, ["match_id", "goal", "on_target", "x", "y", "dist", "angle"]),
                         (self.duels, ["match_id", "def_won", "def_player_id", "att_player_id", "x", "y"])):
            missing = df[cols].isna().sum()
            self.assertEqual(int(missing.sum()), 0, missing[missing > 0].to_dict())

    def test_no_missing_values_after_preprocessing(self):
        """Some raw inputs are missing on purpose (no 360 frame, unknown height). The
        logistic pipeline must turn them into finite numbers before the model sees them."""
        num = models_attack.NUM + models_attack.BOOL + ["height_cm"]
        pre = modeling.logistic(num, models_attack.CAT).named_steps["pre"]
        Z = pre.fit_transform(self.shots[num + models_attack.CAT])
        Z = Z.toarray() if hasattr(Z, "toarray") else Z
        self.assertTrue(np.isfinite(Z).all())
        num_d = models_defense.DUEL_NUM + ["def_height_cm", "att_height_cm", "height_diff"]
        pre = modeling.logistic(num_d, models_defense.DUEL_CAT).named_steps["pre"]
        Z = pre.fit_transform(self.duels[num_d + models_defense.DUEL_CAT])
        Z = Z.toarray() if hasattr(Z, "toarray") else Z
        self.assertTrue(np.isfinite(Z).all())

    def test_labels_are_binary_and_sane(self):
        self.assertTrue(set(self.shots["goal"].unique()) <= {0, 1})
        self.assertTrue((self.shots["goal"] <= self.shots["on_target"]).all(), "every goal is on target")
        self.assertTrue(0.05 < self.shots["goal"].mean() < 0.2)
        self.assertTrue(0.5 < self.duels["def_won"].mean() < 0.7)

    def test_coordinates_on_the_pitch(self):
        for df in (self.shots, self.duels):
            self.assertTrue(df["x"].between(0, 120).all() and df["y"].between(0, 80).all())


@unittest.skipUnless(HAVE_PRED, "predictions not built")
class TestPredictions(unittest.TestCase):
    def test_probabilities_valid_and_calibrated_overall(self):
        d = pd.read_csv(PROC / "duel_predictions.csv.gz")
        for c in ("duel_lr", "duel_gbm"):
            self.assertTrue(d[c].between(0, 1).all())
            self.assertAlmostEqual(d[c].mean(), d["def_won"].mean(), delta=0.005)


class TestStatistics(unittest.TestCase):
    def test_shrinkage_pulls_small_samples_harder(self):
        rng = np.random.default_rng(0)
        rows = []
        for pid in range(300):
            n = 20 if pid < 150 else 400
            skill = rng.normal(0, 0.08)
            p = np.full(n, 0.55)
            rows.append(pd.DataFrame({"player_id": pid, "match_id": rng.integers(0, 2000, n),
                                      "won": (rng.random(n) < p + skill).astype(int), "p": p}))
        g, tau2 = rankings.player_table(pd.concat(rows), "won", "p", 100)
        self.assertGreater(tau2, 0)
        small, big = g[g["n"] == 20]["weight"].mean(), g[g["n"] == 400]["weight"].mean()
        self.assertTrue(0 < small < big < 1)
        self.assertTrue((g["lo95"] <= g["shrunk_rate"]).all() and (g["shrunk_rate"] <= g["hi95"]).all())

    def test_reliability_tells_skill_from_luck(self):
        rng = np.random.default_rng(1)

        def sim(sd):
            rows = []
            for pid in range(150):
                n, skill = 300, rng.normal(0, sd)
                rows.append(pd.DataFrame({"player_id": pid, "match_id": rng.integers(0, 3000, n),
                                          "won": (rng.random(n) < 0.5 + skill).astype(int), "p": 0.5}))
            return pd.concat(rows)
        real = rankings.split_half(sim(0.1), "won", "p", 100, reps=20)["full_length_reliability"]
        luck = rankings.split_half(sim(0.0), "won", "p", 100, reps=20)["full_length_reliability"]
        self.assertGreater(real, 0.6)
        self.assertLess(abs(luck), 0.25)

    def test_mixed_model_recovers_known_spread(self):
        sim = mixed_model.simulation_check(sigma_true=0.4, k=200, n=20000)
        self.assertAlmostEqual(sim["sigma_hat"], 0.4, delta=0.1)
        self.assertGreater(sim["corr_u"], 0.8)


class TestWebsite(unittest.TestCase):
    def test_portuguese_pages_quote_the_same_numbers(self):
        self.assertEqual(check_site_sync.compare(), [])

    def test_number_reader_handles_both_formats(self):
        en = check_site_sync.numbers("<p>10,327 shots, reliability 0.67</p>", "en")
        pt = check_site_sync.numbers("<p>10.327 finalizações, confiabilidade 0,67</p>", "pt")
        self.assertEqual(en, pt)


if __name__ == "__main__":
    unittest.main()
