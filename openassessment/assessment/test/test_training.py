"""
Tests for training models and serializers (common to student and AI training).
"""


from collections import OrderedDict
import copy

from unittest import mock

from django.db import IntegrityError

from openassessment.assessment.models import TrainingExample
from openassessment.assessment.serializers import deserialize_training_examples, serialize_training_example
from openassessment.test_utils import CacheResetTest


class TrainingExampleSerializerTest(CacheResetTest):
    """
    Tests for serialization and deserialization of TrainingExample.
    These functions are pretty well-covered by API-level tests,
    so we focus on edge cases.
    """

    RUBRIC_OPTIONS = [
        {
            "order_num": 0,
            "name": "ππππ",
            "explanation": "π»πππ πππ!",
            "points": 0,
        },
        {
            "order_num": 1,
            "name": "π°πΈπΈπ­",
            "explanation": "ο»­Ρ»Ρ»Ι ο»Ρ»ΰΉ!",
            "points": 1,
        },
        {
            "order_num": 2,
            "name": "ΡΟΒ’ΡββΡΞ·Ρ",
            "explanation": "δΉοΎcδΉοΎοΎδΉεο½² οΎoδΉ!",
            "points": 2,
        },
    ]

    RUBRIC = {
        'prompt': "ΠΠΎΡΠ-βΡΡΠΊ; ΠΎΡ, ΠΠΡ Π©ΠΠ°lΡ",
        'criteria': [
            {
                "order_num": 0,
                "name": "vΓΈΘΌΘΊΖα΅ΎΕΘΊΙΙ",
                "prompt": "Δ¦ΓΈw vΘΊΙΙ¨ΙΔ Ι¨s Ε§Δ§Ι vΓΈΘΌΘΊΖα΅ΎΕΘΊΙΙ?",
                "options": RUBRIC_OPTIONS
            },
            {
                "order_num": 1,
                "name": "ο»­ΙΌΰΈΰΉΰΉΰΈΙΌ",
                "prompt": "π³ππ πππππππ ππ πππ πππππππ?",
                "options": RUBRIC_OPTIONS
            }
        ]
    }

    EXAMPLES = [
        {
            'answer': (
                "πΏππππ πππ πππππππ πππππ πππππ πππ πππππππππ ππ ππππ πππππππ πππππ ππππππ ππ ππππ ππππ"
                " ππππ π πππ πππππ ππππ πππππ ππππππππ πππ π ππππ πππππππππ ππππ, ππππππ πππ πππ πππππππ"
                " ππ πππ πππππ ππππππππ, πππ ππππ ππππ ππππππππ ππππ πππ ππππ ππ ππ ππππππ'π πππππππ πππ πππ πππ."
            ),
            'options_selected': OrderedDict({
                "vΓΈΘΌΘΊΖα΅ΎΕΘΊΙΙ": "π°πΈπΈπ­",
                "ο»­ΙΌΰΈΰΉΰΉΰΈΙΌ": "ππππ",
            })
        },
        {
            'answer': "TΕαΉ-hΓ©Γ‘vΣ³ αΊΓ‘Ε thΓ© ΕhΓ­αΉ Γ‘Ε Γ‘ dΓ­ΕΕΓ©ΕΔΊΓ©ΕΕ ΕtΓΊdΓ©Εt αΊΓ­th Γ‘ΔΊΔΊ ΓΕΓ­ΕtΕtΔΊΓ© Γ­Ε hΓ­Ε hΓ©Γ‘d.",
            'options_selected': OrderedDict({
                "vΓΈΘΌΘΊΖα΅ΎΕΘΊΙΙ": "ππππ",
                "ο»­ΙΌΰΈΰΉΰΉΰΈΙΌ": "ΡΟΒ’ΡββΡΞ·Ρ",
            })
        },
        {
            'answer': (
                "Consider the subtleness of the sea; how its most dreaded creatures glide under water, "
                "unapparent for the most part, and treacherously hidden beneath the loveliest tints of "
                "azure..... Consider all this; and then turn to this green, gentle, and most docile earth; "
                "consider them both, the sea and the land; and do you not find a strange analogy to "
                "something in yourself?"
            ),
            'options_selected': OrderedDict({
                "vΓΈΘΌΘΊΖα΅ΎΕΘΊΙΙ": "ππππ",
                "ο»­ΙΌΰΈΰΉΰΉΰΈΙΌ": "ΡΟΒ’ΡββΡΞ·Ρ",
            })
        },
    ]

    def test_duplicate_training_example(self):
        # Deserialize some examples for a rubric
        deserialize_training_examples(self.EXAMPLES[0:2], self.RUBRIC)

        # Deserialize some more examples, of which two are duplicates
        examples = deserialize_training_examples(self.EXAMPLES, self.RUBRIC)

        # Check that only three examples were created in the database
        db_examples = TrainingExample.objects.all()
        self.assertEqual(len(db_examples), 3)

        # Check that the examples match what we got from the deserializer
        self.assertCountEqual(examples, db_examples)

    def test_similar_training_examples_different_rubric(self):
        # Deserialize some examples
        first_examples = deserialize_training_examples(self.EXAMPLES, self.RUBRIC)

        # Deserialize one more example with the rubric mutated slightly
        mutated_rubric = copy.deepcopy(self.RUBRIC)
        mutated_rubric['criteria'][0]['options'][0]['points'] = 5
        second_examples = deserialize_training_examples(self.EXAMPLES[0:2], mutated_rubric)

        # There should be a total of 5 examples (3 for the first rubric + 2 for the second)
        db_examples = TrainingExample.objects.all()
        self.assertEqual(len(db_examples), 5)

        # Check that each of the examples from the deserializer are in the database
        for example in (first_examples + second_examples):
            self.assertIn(example, db_examples)

    def test_similar_training_examples_different_options(self):
        # Deserialize some examples
        first_examples = deserialize_training_examples(self.EXAMPLES, self.RUBRIC)

        # Deserialize another example that's identical to the first example,
        # with one option changed
        mutated_examples = copy.deepcopy(self.EXAMPLES)
        mutated_examples[0]['options_selected']['vΓΈΘΌΘΊΖα΅ΎΕΘΊΙΙ'] = "ΡΟΒ’ΡββΡΞ·Ρ"
        second_examples = deserialize_training_examples(mutated_examples, self.RUBRIC)

        # Expect that a total of 4 examples (3 for the first call, plus one new example in the second call)
        db_examples = TrainingExample.objects.all()
        self.assertEqual(len(db_examples), 4)

        # Check that all the examples are in the database
        for example in first_examples + second_examples:
            self.assertIn(example, db_examples)

    def test_similar_training_examples_different_answer(self):
        # Deserialize some examples
        first_examples = deserialize_training_examples(self.EXAMPLES, self.RUBRIC)

        # Deserialize another example that's identical to the first example,
        # with a different answer
        mutated_examples = copy.deepcopy(self.EXAMPLES)
        mutated_examples[0]['answer'] = "MUTATED!"
        second_examples = deserialize_training_examples(mutated_examples, self.RUBRIC)

        # Expect that a total of 4 examples (3 for the first call, plus one new example in the second call)
        db_examples = TrainingExample.objects.all()
        self.assertEqual(len(db_examples), 4)

        # Check that all the examples are in the database
        for example in first_examples + second_examples:
            self.assertIn(example, db_examples)

    def test_deserialize_integrity_error(self):
        """
        Simulate an integrity error when creating the training example
        This can occur when using repeatable-read isolation mode.
        """
        example = deserialize_training_examples(self.EXAMPLES[:1], self.RUBRIC)[0]
        with mock.patch('openassessment.assessment.models.TrainingExample.objects.get') as mock_get:
            with mock.patch('openassessment.assessment.models.TrainingExample.create_example') as mock_create:
                mock_get.side_effect = [TrainingExample.DoesNotExist, example]
                mock_create.side_effect = IntegrityError

                # Expect that we get the mock example back
                # (proves that the function tried to retrieve the object again after
                # catching the integrity error)
                examples = deserialize_training_examples(self.EXAMPLES[:1], self.RUBRIC)
                self.assertEqual(examples, [example])

    def test_serialize_training_example_with_legacy_answer(self):
        """Test that legacy answer format in training example serialized correctly"""
        training_examples = deserialize_training_examples(self.EXAMPLES, self.RUBRIC)
        for example in training_examples:
            self.assertIsInstance(example.answer, str)
            serialized_example = serialize_training_example(example)
            self.assertIsInstance(serialized_example["answer"], dict)
            expected_answer_dict = {'parts': [{'text': example.answer}]}
            self.assertEqual(serialized_example["answer"], expected_answer_dict)
