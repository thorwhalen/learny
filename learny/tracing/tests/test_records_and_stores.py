"""Tests for the log-as-source-of-truth contract and the outcome vocabulary.

All fixtures here are synthetic. Real learner data is personal data and never enters
this repository, which is public.
"""

import json

import pytest

from learny.tracing.records import Item, Outcome, Response
from learny.tracing.stores import ResponseLog, data_dir, estimate_store


class TestOutcome:
    def test_skip_is_not_wrong(self):
        """The whole point of a three-valued outcome."""
        assert Outcome.SKIPPED is not Outcome.WRONG
        assert not Outcome.SKIPPED.is_scored
        assert Outcome.WRONG.is_scored

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("correct", Outcome.CORRECT),
            ("unanswered", Outcome.SKIPPED),
            ("BLANK", Outcome.SKIPPED),
            ("incorrect", Outcome.WRONG),
            (True, Outcome.CORRECT),
            (False, Outcome.WRONG),
        ],
    )
    def test_aliases(self, raw, expected):
        assert Outcome(raw) is expected

    def test_unknown_outcome_is_loud(self):
        with pytest.raises(ValueError, match="not a valid outcome"):
            Outcome("maybe")

    def test_serialises_as_plain_string(self):
        assert json.loads(json.dumps({"o": Outcome.CORRECT}))["o"] == "correct"


class TestItem:
    def test_sequence_labels_get_unit_weight(self):
        assert Item("q", labels=("a", "b")).weights == {"a": 1.0, "b": 1.0}

    def test_mapping_labels_keep_their_weight(self):
        assert Item("q", labels={"a": 0.57}).weights == {"a": 0.57}

    def test_difficulty_out_of_range_is_rejected(self):
        with pytest.raises(ValueError, match="difficulty must be in"):
            Item("q", difficulty=1.5)

    def test_difficulty_may_be_unknown(self):
        assert Item("q").difficulty is None


class TestResponseRoundTrip:
    def test_round_trip(self):
        r = Response("ada", "q1", Outcome.CORRECT, at=1.0, meta={"paper": "2004"})
        assert Response.from_dict(r.to_dict()) == r

    def test_tolerates_unknown_keys_from_a_future_version(self):
        d = Response("ada", "q1", "correct").to_dict()
        d["some_field_added_later"] = 42
        assert Response.from_dict(d).student == "ada"

    def test_accepts_a_plain_string_outcome(self):
        assert Response("ada", "q1", "unanswered").outcome is Outcome.SKIPPED


class TestResponseLog:
    def test_append_only_preserves_order(self, tmp_path):
        log = ResponseLog(rootdir=tmp_path)
        for i in range(5):
            log.append(Response("ada", f"q{i}", Outcome.CORRECT, at=float(i)))
        assert [r.item for r in log["ada"]] == [f"q{i}" for i in range(5)]

    def test_students_are_separate_files(self, tmp_path):
        """One file per student: a child's data can be handed over or deleted alone."""
        log = ResponseLog(rootdir=tmp_path)
        log.append(Response("ada", "q1", Outcome.CORRECT))
        log.append(Response("bob", "q1", Outcome.WRONG))
        assert log.students() == ["ada", "bob"]
        assert {p.name for p in tmp_path.glob("*.jsonl")} == {"ada.jsonl", "bob.jsonl"}
        assert [r.student for r in log["ada"]] == ["ada"]

    def test_reopening_does_not_lose_or_rewrite_history(self, tmp_path):
        ResponseLog(rootdir=tmp_path).append(Response("ada", "q1", Outcome.CORRECT))
        ResponseLog(rootdir=tmp_path).append(Response("ada", "q2", Outcome.WRONG))
        assert len(ResponseLog(rootdir=tmp_path)["ada"]) == 2

    def test_missing_student_raises_keyerror(self, tmp_path):
        with pytest.raises(KeyError):
            ResponseLog(rootdir=tmp_path)["nobody"]

    def test_iterating_yields_every_response(self, tmp_path):
        log = ResponseLog(rootdir=tmp_path)
        log.extend(
            [
                Response("ada", "q1", Outcome.CORRECT),
                Response("bob", "q1", Outcome.SKIPPED),
                Response("ada", "q2", Outcome.WRONG),
            ]
        )
        assert len(log) == 3
        assert sorted(r.student for r in log) == ["ada", "ada", "bob"]

    def test_student_name_with_a_slash_does_not_escape_the_root(self, tmp_path):
        log = ResponseLog(rootdir=tmp_path)
        log.append(Response("../escape", "q1", Outcome.CORRECT))
        assert all(p.parent == tmp_path for p in tmp_path.rglob("*.jsonl"))


class TestStoreDefaults:
    def test_data_dir_honours_the_env_override(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LEARNY_DATA_DIR", str(tmp_path))
        assert data_dir("responses") == tmp_path / "responses"

    def test_data_dir_never_defaults_inside_the_package(self, monkeypatch):
        """The default is the policy: state must not land where it can be committed."""
        monkeypatch.delenv("LEARNY_DATA_DIR", raising=False)
        import learny

        pkg_root = __import__("pathlib").Path(learny.__file__).parent.resolve()
        assert pkg_root not in data_dir("responses").resolve().parents

    def test_estimate_store_is_a_mutable_mapping(self, tmp_path):
        store = estimate_store(rootdir=tmp_path)
        store["ada"] = {"ability": 0.3}
        assert store["ada"] == {"ability": 0.3}
        assert "ada" in list(store)
        del store["ada"]
        assert "ada" not in list(store)


# -- choice-game meta: guess rate per response, confusions (#51) ---------------------


def test_per_response_guess_discounts_a_lucky_right_answer():
    """A right pick among 2 options says less than a right pick among 8."""
    from learny.tracing import RaschEstimator, Item, Response

    est = RaschEstimator()
    item = Item("ni", difficulty=0.5)

    def skill_after(k):
        shown = [f"o{i}" for i in range(k)]
        r = Response("ada", "ni", "correct", meta={"pattern": "M1", "shown": shown})
        return est.skill(est.observe(est.init(), r, item)).mu

    plain = est.skill(est.observe(est.init(), Response("ada", "ni", "correct"), item)).mu
    assert 0 < skill_after(2) < skill_after(8) < plain  # no meta: the model-wide guess=0


def test_model_wide_guess_still_applies_without_meta():
    from learny.tracing import RaschEstimator, Item, Response

    item = Item("q", difficulty=0.5)
    r = Response("ada", "q", "wrong")
    a = RaschEstimator(guess=0.25)
    b = RaschEstimator()
    with_meta = Response("ada", "q", "wrong", meta={"guess": 0.25})
    assert a.observe(a.init(), r, item) == b.observe(b.init(), with_meta, item)


def test_confusions_counts_only_wrong_picks():
    from learny.tracing import Response, confusions

    log = [
        Response("ada", "tsu", "wrong", meta={"chosen": "shi"}),
        Response("bo", "tsu", "wrong", meta={"chosen": "shi"}),
        Response("ada", "tsu", "skipped", meta={"chosen": "shi"}),
        Response("ada", "tsu", "correct", meta={"chosen": "tsu"}),
    ]
    assert confusions(log) == {("tsu", "shi"): 2}
    assert confusions(r for r in log if r.student == "ada") == {("tsu", "shi"): 1}


def test_choice_meta_round_trips():
    from learny.tracing import CHOICE_META_KEYS, Response

    meta = dict.fromkeys(CHOICE_META_KEYS, "x") | {"shown": ["a", "b"], "guess": 0.5, "extra": 1}
    r = Response("ada", "a", "correct", meta=meta)
    assert Response.from_dict(r.to_dict()) == r


def test_prequential_forecasts_at_each_rounds_own_guess():
    """A forecast is judged at the rate the update learned from (#51)."""
    from learny.tracing import Item, RaschEstimator, Response, prequential

    items = {"q": Item("q", difficulty=0.5)}
    two = {"pattern": "M1", "shown": ["q", "x"]}
    rs = [Response("a", "q", "correct", meta=two)]
    [(_, p)] = prequential(rs, items=items, estimator=RaschEstimator())
    assert p == 0.5 + 0.5 * 0.5  # cold start: half the time known, else a coin flip
