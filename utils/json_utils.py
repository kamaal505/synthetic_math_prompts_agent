import json
import re

try:
    import json_repair
except ImportError:
    json_repair = None

from core.llm.openai_utils import call_openai_model
from utils.exceptions import JSONParsingError
from utils.logging_config import get_logger

# Get logger instance
logger = get_logger(__name__)


def _initial_json_cleaning(raw_text):
    """
    Performs initial cleaning of raw text to extract and prepare JSON content.
    This includes the same cleaning logic as the original safe_json_parse function.
    """
    raw_text = raw_text.strip()

    # Strip Markdown-style fencing
    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
    raw_text = re.sub(r"\s*```$", "", raw_text)

    # Trim to { ... } block if there's garbage around
    json_start = raw_text.find("{")
    json_end = raw_text.rfind("}") + 1
    if json_start == -1 or json_end == -1:
        raise JSONParsingError("No JSON block detected.")
    raw_text = raw_text[json_start:json_end]

    # Fix invalid quote escaping (e.g., \" inside a value)
    raw_text = raw_text.replace('\\"', '"')

    # Escape LaTeX-style backslashes
    raw_text = re.sub(r'(?<!\\)\\(?![\\nt"\\/bfr])', r"\\\\", raw_text)

    return raw_text


def _attempt_json_repair_with_library(malformed_json):
    """
    Attempts to repair malformed JSON using the json-repair library.
    Returns the repaired JSON string if successful, None otherwise.
    """
    if json_repair is None:
        logger.debug("json-repair library not available, skipping automated repair")
        return None

    try:
        logger.debug("Attempting automated JSON repair with json-repair library")
        repaired_json = json_repair.repair(malformed_json)
        # Test if the repaired JSON is valid
        json.loads(repaired_json)
        logger.debug("✅ Automated JSON repair successful")
        return repaired_json
    except (ValueError, json.JSONDecodeError, Exception) as e:
        logger.debug(f"❌ Automated JSON repair failed: {e}")
        return None


def _attempt_json_repair_with_llm(malformed_json):
    """
    Attempts to repair malformed JSON using an LLM call.
    Returns the repaired JSON string if successful, None otherwise.
    """
    try:
        logger.debug("Attempting LLM-based JSON repair")

        # Construct the repair prompt as specified in the architectural plan
        system_prompt = (
            "You are an expert JSON fixer. Your sole task is to correct any syntax errors "
            "in the provided text to make it a valid JSON object. Do not add any new information "
            "or alter the existing data. Only output the corrected JSON."
        )

        user_prompt = (
            f"Please fix the following JSON:\n\n```json\n{malformed_json}\n```"
        )

        # Combine system and user prompts for the LLM call
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        # Use a lightweight model for JSON repair (o3-mini is fast and cost-effective)
        result = call_openai_model(
            role="system", prompt=full_prompt, model_name="o3-mini", effort="low"
        )

        if result and result.get("output"):
            llm_output = result["output"]
            logger.debug("✅ LLM-based JSON repair completed, testing validity")

            # Run the LLM output through initial cleaning and parsing again
            cleaned_output = _initial_json_cleaning(llm_output)
            # Test if the repaired JSON is valid
            json.loads(cleaned_output)
            logger.debug("✅ LLM-repaired JSON is valid")
            return cleaned_output
        else:
            logger.debug("❌ LLM returned empty or invalid response")
            return None

    except Exception as e:
        logger.debug(f"❌ LLM-based JSON repair failed: {e}")
        return None


def safe_json_parse(raw_text):
    """
    Robust JSON parsing function with multi-layered repair strategy.

    This function implements a comprehensive approach to parsing potentially malformed JSON:
    1. Initial cleaning (markdown removal, trimming, escaping)
    2. Direct parsing attempt
    3. Automated repair using json-repair library
    4. LLM-based repair as fallback
    5. Comprehensive error logging and exception raising

    Args:
        raw_text (str): Raw text potentially containing JSON

    Returns:
        dict: Parsed JSON object

    Raises:
        JSONParsingError: If all repair attempts fail
    """
    original_text = raw_text
    repair_attempts = []

    try:
        # Step 1: Initial cleaning
        logger.debug("Step 1: Performing initial JSON cleaning")
        cleaned_text = _initial_json_cleaning(raw_text)

        # Step 2: Direct parsing attempt
        logger.debug("Step 2: Attempting direct JSON parsing")
        try:
            result = json.loads(cleaned_text)
            logger.debug("✅ Direct JSON parsing successful")
            return result
        except json.JSONDecodeError as e:
            logger.debug(f"❌ Direct JSON parsing failed: {e}")
            repair_attempts.append(f"Direct parse failed: {e}")

        # Step 3: Automated repair with json-repair library
        logger.debug("Step 3: Attempting automated JSON repair")
        repaired_with_library = _attempt_json_repair_with_library(cleaned_text)
        if repaired_with_library is not None:
            try:
                result = json.loads(repaired_with_library)
                logger.debug("✅ JSON parsing successful after automated repair")
                return result
            except json.JSONDecodeError as e:
                logger.debug(f"❌ Automated repair produced invalid JSON: {e}")
                repair_attempts.append(f"json-repair library failed: {e}")
        else:
            repair_attempts.append(
                "json-repair library failed: No repair attempted or library unavailable"
            )

        # Step 4: LLM-based repair
        logger.debug("Step 4: Attempting LLM-based JSON repair")
        repaired_with_llm = _attempt_json_repair_with_llm(cleaned_text)
        if repaired_with_llm is not None:
            try:
                result = json.loads(repaired_with_llm)
                logger.debug("✅ JSON parsing successful after LLM repair")
                return result
            except json.JSONDecodeError as e:
                logger.debug(f"❌ LLM repair produced invalid JSON: {e}")
                repair_attempts.append(f"LLM-based repair failed: {e}")
        else:
            repair_attempts.append("LLM-based repair failed: No valid repair produced")

        # Step 5: Final fallback - comprehensive error logging
        logger.error("🚨 All JSON repair attempts failed")
        logger.error(f"📄 Original text: {original_text[:200]}...")
        logger.error(f"🧹 Cleaned text: {cleaned_text[:200]}...")
        logger.error("🔧 Repair attempts:")
        for i, attempt in enumerate(repair_attempts, 1):
            logger.error(f"   {i}. {attempt}")

        raise JSONParsingError(
            f"All JSON parsing and repair attempts failed. "
            f"Attempts made: {len(repair_attempts)}. "
            f"Last error: {repair_attempts[-1] if repair_attempts else 'Unknown'}"
        )

    except JSONParsingError:
        # Re-raise JSONParsingError as-is
        raise
    except Exception as e:
        # Catch any unexpected errors and wrap them
        logger.error(f"🚨 Unexpected error during JSON parsing: {e}")
        raise JSONParsingError(f"Unexpected error during JSON parsing: {e}")
