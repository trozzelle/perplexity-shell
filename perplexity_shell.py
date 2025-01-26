import argparse
import logging
import os
import sys
import urllib.request
import urllib.error
import json
from typing import Any, Dict
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.logging import RichHandler
import re


def setup_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO

    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            RichHandler(rich_tracebacks=True, markup=True),
            logging.FileHandler(os.path.join(log_dir, "perplexity.log")),
        ],
    )


class TerminalFormatter:
    """Handle terminal output formatting using Rich"""

    def __init__(self):
        self.console = Console()
        self.logger = logging.getLogger(__name__)

    def format_response(self, data: Dict[str, Any]) -> None:
        """Format the JSON response for terminal output using Rich"""
        try:
            # Create markdown content
            markdown_content = []

            # Add explanation
            explanation = data.get("explanation", "")
            if explanation:
                markdown_content.append(explanation)
                markdown_content.append("\n")  # Add spacing

            # Add examples
            examples = data.get("examples", [])
            if examples:
                markdown_content.append("### Examples\n")
                for example in examples:
                    # Check if example is a dict with code
                    if isinstance(example, dict) and "code" in example:
                        markdown_content.append(f"**{example.get('description', '')}**")
                        markdown_content.append(f"```\n{example['code']}\n```")
                    else:
                        markdown_content.append(f"* {example}")
                    markdown_content.append("")  # Add spacing between examples

            # Convert to markdown and print
            md = Markdown("\n".join(markdown_content))
            self.console.print(Panel(md, border_style="blue"))

        except Exception as e:
            self.logger.error(f"Failed to format response: {e}")
            self.console.print(str(data), style="red")


def parse_perplexity_response(raw_response: str) -> Dict[str, Any]:
    if '"content":' in raw_response:
        outer_json = json.loads(raw_response)
        text = outer_json["choices"][0]["message"]["content"]
    else:
        text = raw_response

    match = re.search(r"({[^}]*}(?:[^}]*})*)", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found")

    json_str = match.group(1)

    def replace_newlines(m):
        s = m.group(1)
        s = re.sub(r"(?<!\\)\n", "{{NEWLINE}}", s)
        return s

    json_str = re.sub(r'("(?:\\.|[^"\\])*")', replace_newlines, json_str)
    json_str = re.sub(r"[\x00-\x09\x0b-\x1F]", " ", json_str)

    try:
        result = json.loads(json_str)
    except json.JSONDecodeError:
        json_str = json_str.encode().decode("unicode_escape")
        result = json.loads(json_str)

    def restore_newlines(obj):
        if isinstance(obj, dict):
            return {k: restore_newlines(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [restore_newlines(item) for item in obj]
        elif isinstance(obj, str):
            return obj.replace("{{NEWLINE}}", "\n")
        return obj

    return restore_newlines(result)


def query_perplexity(query: str, api_key: str) -> Dict[str, Any]:
    """Construct the request, send it to Perplexity, and return the response"""
    logger = logging.getLogger(__name__)
    url = "https://api.perplexity.ai/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response_schema = {
        "type": "json_schema",
        "json_schema": {
            "schema": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": "Main explanation text",
                    },
                    "examples": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of examples or key points",
                    },
                },
                "required": ["explanation", "examples"],
            }
        },
    }

    payload: Dict[str, Any] = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": "Provide clear, structured responses with an explanation and practical examples. Please output a JSON object with the following fields: explanation, examples.",
            },
            {"role": "user", "content": query},
        ],
        "response_format": response_schema,
    }

    logger.debug(payload)
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    logger.debug(f"Sending request: {request}")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status != 200:
                raise ValueError(f"API request failed with status {response.status}")

            response_body = response.read().decode("utf-8")
            try:
                content = parse_perplexity_response(response_body)
                return content
            except Exception as e:
                logger.error(f"Failed to parse perplexity response: {e}")
            # response_json = json.loads(response_body)
            # logger.debug(f"Response body: {response_body}")
            # try:
            #     if "choices" in response_json and len(response_json["choices"]) > 0:
            #         # Escapes the newlines often included in Perplexity's response
            #         logger.debug(f"Choices: {response_json['choices']}")
            #         content = json.dumps(
            #             response_json["choices"][0]["message"]["content"]
            #         )
            #         logger.info(f"Choices to str: {content}")
            #
            #         return json.loads(json.loads(content))
            #     return {"explanation": "No result from Perplexity."}
            # except json.decoder.JSONDecodeError:
            #     logger.error(f"Failed to decode choices: {content}")

    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        logger.error(f"Request error: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        logger.debug(f"Problematic JSON string: {response_body}")
        raise ValueError(f"Invalid JSON response: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Search using Perplexity AI")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--api_key", help="Perplexity API key")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    setup_logging(args.debug)
    logger = logging.getLogger(__name__)

    logger.debug("Arguments: " + str(args))

    api_key = args.api_key or os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No API key provided. Set PERPLEXITY_API_KEY environment variable."
        )

    try:
        formatter = TerminalFormatter()
        response = query_perplexity(args.query, api_key)
        formatter.format_response(response)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
