import argparse
import logging
import os
import sys
import urllib.request
import urllib.error
import json
from typing import Any, Dict, Tuple
from rich.console import Console, Group
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.logging import RichHandler
from rich.align import Align
from rich.text import Text
from rich.table import Table
from rich import box
from rich.padding import Padding
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
        self.console = Console(markup=True)
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _format_citations(citations: Dict[str, Any], content: str) -> str:
        """Adds citations url to footnote annotation"""

        for i, citation in enumerate(citations, start=1):
            citation_url = citation if citation else "#"
            content = re.sub(
                f"\\[{i}\\]",
                f"[link={citation_url}][cyan][{i}][/cyan][/link]",
                content,
            )

        return content

    def format_response(self, data: Dict[str, Any], citations: Dict[str, Any]) -> None:
        """Format the JSON response for terminal output using Rich"""
        try:
            # This will hold the rich renderables
            rich_content = []

            # Add explanation (main text)
            explanation_table = Table(
                box=None,
                expand=False,
                show_header=False,
                show_edge=False,
                pad_edge=False,
            )
            explanation = data.get("explanation", "")

            # Format the citations in the explanation text
            if explanation and citations:
                explanation = self._format_citations(citations, explanation)

            # Add to renderables list
            if explanation:
                explanation_table.add_row(explanation)
                rich_content.append(Padding(explanation_table, (0, 0, 3, 0)))

            # Add additional notes (examples)
            notes = data.get("examples", [])
            if notes:
                notes_table = Table(
                    box=None,
                    expand=False,
                    # show_header=False,
                    show_edge=False,
                    pad_edge=False,
                    # padding=(0, 0, 1, 0),
                )
                notes_table.title = "[green][b][u]Notes[/u][/b][/green]"

                # This whole section needs to be cleaned up
                notes_string = ""
                notes_renderables = []

                for note in notes:
                    # Format citations in the example text
                    if isinstance(note, str) and citations:
                        note = self._format_citations(citations, note)

                    # Check if note is a dict with code
                    if isinstance(note, dict) and "code" in note:
                        notes_renderables.append(f"{note.get('description', '')}\n")
                        code = note.get("code", "")
                        lexer = Syntax.guess_lexer(code)
                        syntax = Syntax(note.get("code", ""), lexer=lexer)
                        notes_renderables.append(syntax)
                        notes_renderables.append("\n")
                    else:
                        notes_string += f"[yellow]•[/yellow] {note}" + "\n\n"
                notes_table.add_row(
                    notes_string if notes_string else Group(*notes_renderables)
                )
                notes_aligned = Align(notes_table, "center")
                rich_content.append(notes_aligned)

            # Group the renderables, wrap in an Align constructor,
            # then wrap in a Panel constructor and print
            panel = Panel(
                Align.center(Group(*rich_content), vertical="middle"),
                box=box.ROUNDED,
                border_style="blue",
                padding=(1, 2),
                title="[cyan]Perplexity Shell[/cyan]",
                title_align="center",
            )
            self.console.print(panel)

        except Exception as e:
            self.logger.error(f"Failed to format response: {e}")
            self.console.print(str(data), style="red")


def parse_perplexity_response(raw_response: str) -> Dict[str, Any]:
    # Perplexity's API often responds with a json string
    # that has nested escaping. Gnarly stuff like
    #
    #  {\n      \"name\": \"Processing multi-line records\", \n
    #   \"code\": \"awk 'BEGIN {RS=\\\"\\\\n\\\\n\\\"; FS=\\\"\\\\n\\\"}
    # {print $1}' file.txt\",\n
    #
    # This is supposed to reflect the eventual formatting
    # but is a nightmare to work with. Here, we handle it
    # by replacing the control characters but preserving the
    # newlines. A better approach would probably be to
    # recursively unescape the content and build the JSON
    # inside-out.
    #
    # I don't like how fragile this is because Perplexity could
    # change the response structure (and probably should) at
    # any moment so hopefully this will be replaced in the
    # future with something more robust.
    if '"content":' in raw_response:
        # If key exists, assume its the raw http response and parse
        outer_json = json.loads(raw_response)
        text = outer_json["choices"][0]["message"]["content"]
    else:
        # If it doesn't, assume this is the content itself
        text = raw_response

    # Matches the JSON object, since sometimes the
    # API will response with 'Here is the JSON object: {..."
    match = re.search(r"({[^}]*}(?:[^}]*})*)", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found")

    json_str = match.group(1)

    # To preserve nested escaped newlines, we sometimes
    # temporarily replace them with a valid stand-in
    # and then restore them at the end
    def replace_newlines(m):
        s = m.group(1)
        s = re.sub(r"(?<!\\)\n", "{{NEWLINE}}", s)
        return s

    json_str = re.sub(r'("(?:\\.|[^"\\])*")', replace_newlines, json_str)

    # Removes any remaining control characters
    json_str = re.sub(r"[\x00-\x09\x0b-\x1F]", " ", json_str)

    # Not sure this is still necessary
    try:
        result = json.loads(json_str)
    except json.JSONDecodeError:
        json_str = json_str.encode().decode("unicode_escape")
        result = json.loads(json_str)

    # Recursively restore the newlines we had previously replaced
    def restore_newlines(obj):
        if isinstance(obj, dict):
            return {k: restore_newlines(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [restore_newlines(item) for item in obj]
        elif isinstance(obj, str):
            return obj.replace("{{NEWLINE}}", "\n")
        return obj

    return restore_newlines(result)


def query_perplexity(query: str, api_key: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
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
            logger.debug(f"Response body: {response_body}")
            try:
                content = parse_perplexity_response(response_body)
                logger.debug(f"Content body: {content}")
                citations = json.loads(response_body)["citations"]
                return content, citations
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
        content, citations = query_perplexity(args.query, api_key)
        formatter.format_response(content, citations)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
