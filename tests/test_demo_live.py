"""Integration checks for the live adapter without making external model calls."""
import copy
import unittest
from unittest.mock import patch

from demo import live, server


class LiveDemoTest(unittest.TestCase):
    def setUp(self):
        self.case = server.case_detail("HCMA011063142025")
        self.facts = server.sharded("rq2_fresh")["HCMA011063142025"]["facts"]
        self.text = "\n\n".join(f"{p['n']}. {p['text']}" for p in self.case["paragraphs"])

    def test_unquoted_model_date_is_removed_before_checker(self):
        facts = copy.deepcopy(self.facts)
        facts["order"]["date"] = {"value": "2099-01-01", "quote": "order dated 2099-01-01", "para": 1}
        grounded, counts = live.ground_facts(facts, self.case["paragraphs"])
        self.assertIsNone(grounded["order"]["date"]["value"])
        self.assertGreaterEqual(counts["ungrounded_items_removed"], 1)

    def test_real_pipeline_streams_tools_checks_and_final_result(self):
        facts = self.facts

        def fake_complete(backend, messages, **kwargs):
            tag = kwargs["tag"]
            if tag == "demo:live_facts":
                answer = facts
            elif tag.endswith(":plan"):
                answer = {"tool_calls": [{"tool": "statute_lookup", "args": {"ref": "CGST Act s.75(4)"}}],
                          "missing_facts": []}
            else:
                types = kwargs["json_schema"]["properties"]["findings"]["items"]["properties"]["type"]["enum"]
                answer = {"findings": [{"type": kind, "verdict": "cant_tell", "evidence": [],
                                        "missing_facts": ["not stated in verified record"], "confidence": 0.0}
                                       for kind in types]}
            self.assertFalse(kwargs["use_cache"])
            return {"json": answer, "model": "gemini-test-stub", "tokens_in": 0,
                    "tokens_out": 0, "seconds": 0.0}

        events = []
        with patch("demo.live.complete", fake_complete), patch("src.noticecheck.pipeline.complete", fake_complete):
            result = live.run_live(self.text, events.append)

        kinds = [event["type"] for event in events]
        self.assertEqual(kinds[0], "input")
        self.assertEqual(kinds[-1], "result")
        self.assertLess(kinds.index("extraction"), kinds.index("step"))
        steps = [event["step"] for event in events if event["type"] == "step"]
        self.assertTrue(any(s.get("tool") == "statute_lookup" and s.get("output") for s in steps))
        self.assertEqual(sum(bool(s.get("defect")) and s["stage"] == "precondition_check" for s in steps), 13)
        self.assertTrue(any(s["stage"] == "verify" for s in steps))
        self.assertEqual(len(result["findings"]), 13)
        self.assertEqual(result["mode"], "live_gemini")

    def test_checker_comparison_replays_the_same_noticecheck_run(self):
        case = server.case_detail("HCMD010677412024")
        self.assertEqual(case["run"], "nc_full_s2")
        self.assertEqual(case["comparison"]["input"]["view"], "full_record")
        self.assertEqual(case["comparison"]["plain"]["cnr"], case["main"]["cnr"])
        self.assertEqual(case["trace"], server.trace(case["main"]))
        self.assertNotIn("rq2", case)
        self.assertEqual([p["n"] for p in case["paragraphs"]], [0, 2, 3, 4, 5, 6, 7])
        hearing_quote = next(f for f in case["main"]["findings"] if f["type"] == "hearing_75_4")["evidence"][0]["quote"]
        self.assertIn(hearing_quote, case["paragraphs"][2]["text"])


if __name__ == "__main__":
    unittest.main()
