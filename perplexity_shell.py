import argparse
import logging
import os
import sys
import urllib.request
import urllib.error
import json
from typing import Any, Dict


class TerminalFormatter:
    """Handle terminal output formatting with ANSI color codes"""

    BLUE = "\033[0;34m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[0;33m"
    GRAY = "\033[0;90m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    @classmethod
    def format_response(cls, response_json: str) -> str:
        """Format the JSON response for terminal output"""
        try:
            output = []

            # Add header separator
            output.append(f"\n{cls.BLUE}{'━' * 50}{cls.RESET}\n")

            # Main explanation
            explanation = response_json.get("explanation", "")
            if explanation:
                # Split long text into paragraphs for better readability
                paragraphs = explanation.split("\n\n")  # Split on double newlines
                for para in paragraphs:
                    output.append(f"{cls.BOLD}{para.strip()}{cls.RESET}\n")

            # Examples
            examples = response_json.get("examples", [])
            if examples:
                output.append(f"\n{cls.YELLOW}Examples:{cls.RESET}")
                for example in examples:
                    output.append(f"  • {cls.GREEN}{example}{cls.RESET}")
                output.append("")

            # Add footer separator
            output.append(f"\n{cls.BLUE}{'━' * 50}{cls.RESET}\n")

            return "\n".join(output)

        except Exception as e:
            logging.error(f"Failed to format response: {e}")
            return str(response_json)

        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse response JSON: {e}")
            return str(response_json)
        except Exception as e:
            logging.error(f"Failed to format response response: {e}")
            return str(response_json)


def query_perplexity(query: str, api_key: str) -> str:
    """Construct the request, send it to Perplexity, and return the response"""
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

    data = json.dumps(payload).encode("utf-8")
    print(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    # response = urllib.request.urlopen(request, timeout=5)
    # print(response.read().decode("utf-8"))
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status != 200:
                raise ValueError(f"API request failed with status {response.status}")

            # Parse the API response
            response_body = response.read().decode("utf-8")
            response_json = json.loads(response_body)
            print(response_json)
            if "choices" in response_json and len(response_json["choices"]) > 0:
                # Get the content string which contains our nested JSON
                content = response_json["choices"][0]["message"]["content"]
                # Parse the nested JSON content
                content_json = json.loads(content)
                return TerminalFormatter.format_response(content_json)
            return "No result from Perplexity."

    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        logging.error(f"Request error: {e}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error: {e}")
        raise ValueError(f"Invalid JSON response: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Search using Perplexity AI")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--api_key", help="Perplexity API key")
    parser.add_argument("--raw", action="store_true", help="Output raw JSON response")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No API key provided. Set PERPLEXITY_API_KEY environment variable."
        )

    try:
        response = query_perplexity(args.query, api_key)
        print(response)
    except Exception as e:
        logging.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
