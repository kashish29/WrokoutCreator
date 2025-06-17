import json
import google.generativeai as genai
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


GEMINI_MODELS = {
    "gemini-2.0-flash-001": {
        "id": "gemini-2.0-flash-001", "name": "Gemini 2.0 Flash",
        "inputPrice": 0.1, "outputPrice": 0.4
    },
    "gemini-1.5-flash-002": {
        "id": "gemini-1.5-flash-002", "name": "Gemini 1.5 Flash (128k+)",
        "inputPrice": 0.075, "outputPrice": 0.3 # Using first tier pricing
    },
    "gemini-2.5-pro-preview-06-05": {
        "id": "gemini-2.5-pro-preview-06-05", "name": "Gemini 2.5 Pro Preview (200k+)",
        "inputPrice": 1.25, "outputPrice": 10 # Using first tier pricing
    },
    "gemini-2.5-flash-preview-05-20": {
        "id": "gemini-2.5-flash-preview-05-20", "name": "Gemini 2.5 Flash Preview",
        "inputPrice": 0.15, "outputPrice": 0.6
    },
    # Adding a few more for variety, focusing on priced models
    "gemini-1.5-pro-latest": {
		"id": "gemini-1.5-pro-latest", "name": "Gemini 1.5 Pro",
		"inputPrice": 3.5, "outputPrice": 10.5
	},
    "gemini-1.5-flash-latest": {
		"id": "gemini-1.5-flash-latest", "name": "Gemini 1.5 Flash",
		"inputPrice": 0.35, "outputPrice": 0.70
	},
}
DEFAULT_MODEL_ID = "gemini-2.0-flash-001"

class SimpleGeminiProvider:
    def __init__(self, options):
        if not options.get("gemini_api_key"):
            raise ValueError("Gemini API key is required.")
        
        self.options = options
        genai.configure(api_key=options["gemini_api_key"])
        
        self.model_id = options.get("model_id", DEFAULT_MODEL_ID)
        self.model_info = GEMINI_MODELS.get(self.model_id)
        if not self.model_info:
            raise ValueError(f"Unsupported model ID: {self.model_id}")
            
        self.model = genai.GenerativeModel(
            self.model_id,
            generation_config={
                "max_output_tokens": options.get("model_max_tokens"),
                "temperature": options.get("model_temperature", 0.5),
                "response_mime_type": "application/json",
            }
        )

    def create_message_stream(self, system_instruction, user_prompt):
        full_prompt = f"{system_instruction}\n\n{user_prompt}"
        
        try:
            # The Python SDK doesn't have the same usage metadata stream.
            # We will calculate tokens based on the final response.
            response_stream = self.model.generate_content(full_prompt, stream=True)

            for chunk in response_stream:
                if chunk.text:
                    yield json.dumps({"type": "text", "text": chunk.text}) + "\n"
            
            yield json.dumps({"type": "usage", "inputTokens": 0, "outputTokens": 0, "totalCost": 0}) + "\n"

        except Exception as e:
            logger.error(f"Gemini stream generation failed: {e}")
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"


    def calculate_cost(self, input_tokens, output_tokens):
        input_cost = (input_tokens / 1_000_000) * self.model_info["inputPrice"]
        output_cost = (output_tokens / 1_000_000) * self.model_info["outputPrice"]
        return input_cost + output_cost