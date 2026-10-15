from types import SimpleNamespace
import unittest

from b1.pln_worker import ANSWER_GENERATION_FAILURE, answer_generation_errors, bind_component_lms
from b1.records import pln_label


class ComponentLMTests(unittest.TestCase):
    def test_parser_and_answer_generator_share_the_audited_lm(self):
        assigned = []
        parser = SimpleNamespace(_module=SimpleNamespace(set_lm=assigned.append))
        predictor = SimpleNamespace(lm="uncontrolled")
        service = SimpleNamespace(_answer_gen=SimpleNamespace(_predict=predictor))
        audited_lm = object()

        bind_component_lms(service, parser, audited_lm)

        self.assertEqual(assigned, [audited_lm])
        self.assertIs(predictor.lm, audited_lm)

    def test_missing_answer_predictor_fails_closed(self):
        with self.assertRaisesRegex(AttributeError, "answer generator"):
            bind_component_lms(SimpleNamespace(_answer_gen=object()), object(), object())

    def test_answer_failure_sentinel_can_be_classified_as_an_error(self):
        response = {"raw_proof": "['proof']", "answer": ANSWER_GENERATION_FAILURE}
        errors = answer_generation_errors(response, "query:q1")
        self.assertEqual(errors[0]["phase"], "query:q1")
        self.assertEqual(pln_label({"raw_proof": "['proof']"}, errors),
                         ("ERROR", "answer_generation_error"))

    def test_no_proof_answer_does_not_require_generation(self):
        response = {"raw_proof": "[]", "answer": "I don't know"}
        self.assertEqual(answer_generation_errors(response, "query:q1"), [])


if __name__ == "__main__":
    unittest.main()
