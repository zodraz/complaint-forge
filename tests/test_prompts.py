import unittest

from langchain_core.prompts import ChatPromptTemplate

from prompts.system_prompts import ANALYZER_PROMPT, TRIAGE_PROMPT


class PromptTemplateTests(unittest.TestCase):
    def test_triage_prompt_only_requires_input(self):
        prompt = ChatPromptTemplate.from_template(TRIAGE_PROMPT)

        self.assertEqual(prompt.input_variables, ["input"])

    def test_analyzer_prompt_requires_complaint_and_history(self):
        prompt = ChatPromptTemplate.from_template(ANALYZER_PROMPT)

        self.assertEqual(set(prompt.input_variables), {"complaint", "history"})


if __name__ == "__main__":
    unittest.main()
