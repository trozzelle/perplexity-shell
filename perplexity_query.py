import argparse
import logging
import os
import sys
import urllib.request
import urllib.error
import json
from typing import Any, Dict

# Second stage of the script

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


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
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {
                "role": "system",
                "content": "Provide clear, structured responses with an explanation and practical examples.",
            },
            {"role": "user", "content": query},
        ],
        "response_format": response_schema,
    }

    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    # response = urllib.request.urlopen(request, timeout=5)
    # print(response.read().decode("utf-8"))
    try:
        logging.info(f"Sending request to {url}")
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status != 200:
                raise ValueError(
                    f"API request failed with status code {response.status}. "
                    "Additional info: " + response.read().decode("utf-8")
                )

            response_body = response.read().decode("utf-8")
            response_json = json.loads(response_body)
            # result = response_json.get("completion", "No result from Perplexity.")
            # return result

            if "choices" in response_json and len(response_json["choices"]) > 0:
                return response_json["choices"][0]["message"]["content"]
            else:
                return "No result from Perplexity."

    except urllib.error.HTTPError as http_error:
        logging.error(f"HTTP error: {http_error}")
        raise ValueError(f"HTTP error: {http_error}") from http_error

    except urllib.error.URLError as url_error:
        logging.error(f"URL error: {url_error}")
        raise

    except json.JSONDecodeError as json_error:
        logging.error(f"JSON decode error: {json_error}")
        raise ValueError(f"Invalid JSON response: {json_error}") from json_error


def file_info(query: str, api_key: str, params) -> str:
    pass


def cmd_help(query: str, api_key: str, params) -> str:
    """Prompt for pxhelp"""
    try:
        prompt = f"""
            Command type: {params["cmd_type"]}
            Man page exists: {'yes' if params["man_exists"] else 'no'}
            
            Question: ${query}
            
            Please provide a clear explanation and practical examples."
                """

        return query_perplexity(prompt, api_key)
    except Exception as e:
        logging.error(f"Error occurred: ${e}")


def main() -> None:
    """Args are passed from the first stage of the script"""
    parser = argparse.ArgumentParser(description="Query Perplexity from your shell.")
    parser.add_argument("--query", required=True, help="Query to perplexity.")
    parser.add_argument("--api_key", required=True, help="Perplexity API key.")
    parser.add_argument("--mode", choices=["file_info", "cmd_help"], help="Query mode.")
    parser.add_argument("--command", help="Command.")
    parser.add_argument("--cmd_type", help="Type of command.")
    parser.add_argument(
        "--man_exists",
        type=bool,
        default=False,
        help="Check if the query has a man page.",
    )
    parser.add_argument("--file_type", help="File type.")
    parser.add_argument("--file_size", help="File size.")
    parser.add_argument("--file_created", help="File created.")
    args = parser.parse_args()

    print(args)

    api_key = args.api_key or os.environ.get("PERPLEXITY_API_KEY")
    response = ""

    if not api_key:
        logging.error(
            "No API key provided. Please provide one with the --api_key argument or set the PERPLEXITY_API_KEY environment variable."
        )
        raise RuntimeError(
            "No API key provided. Please provide one with the --api_key argument."
        )

    if args.mode == "file_info":
        params = {
            "file_type": args.file_type or "",
            "file_size": args.file_size or "",
            "file_created": args.file_created or "",
        }

        file_info(args.query, api_key, params)

    elif args.mode == "cmd_help":
        params = {
            "cmd_type": args.cmd_type or "",
            "man_exists": args.man_exists or "",
        }

        response = cmd_help(args.query, api_key, params)

    print(response)


if __name__ == "__main__":
    main()
