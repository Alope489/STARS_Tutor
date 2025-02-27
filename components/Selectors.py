# Custom selector with logging
import logging
from langchain.prompts.example_selector.semantic_similarity import SemanticSimilarityExampleSelector

class LoggingSemanticSimilarityExampleSelector(SemanticSimilarityExampleSelector):
    def select_examples(self, input_variables):
        logging.info("Few-shot examples selected.")
        return super().select_examples(input_variables)