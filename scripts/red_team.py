from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

import yaml
from loguru import logger

from agents.core_agent import SafeFunctionCallingAgent, build_core_agent
from vocode.streaming.agent.chat_gpt_agent import ChatGPTAgent
from server.state_manager import StateManager
from tools.safety import safety_check

PROMPTS_FILE = Path(__file__).with_name("red_prompts.yml")


def load_prompts(path: Path | str = PROMPTS_FILE) -> List[str]:
    """Return list of prompts from the given YAML file."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, list):
        raise ValueError("Prompt file must contain a YAML list")
    return [str(p) for p in data]


async def _gather_text(generator: Any) -> str:
    parts: List[str] = []
    async for resp in generator:
        if hasattr(resp.message, "text"):
            parts.append(getattr(resp.message, "text"))
    return "".join(parts)


async def evaluate_prompt(
    agent: SafeFunctionCallingAgent, prompt: str, conversation_id: str
) -> Dict[str, Any]:
    """Return raw response and allow/deny verdict for a single prompt."""
    raw = await _gather_text(
        ChatGPTAgent.generate_response(agent, prompt, conversation_id)
    )
    allowed = safety_check(raw)
    return {"prompt": prompt, "response": raw, "allowed": allowed}


async def run_red_team(prompts: List[str]) -> List[Dict[str, Any]]:
    state_manager = StateManager()
    config = build_core_agent(state_manager)
    agent = SafeFunctionCallingAgent(config.agent, state_manager=state_manager)
    results = []
    for idx, prompt in enumerate(prompts):
        logger.info("Testing prompt %d", idx + 1)
        results.append(await evaluate_prompt(agent, prompt, str(idx)))
    return results


def summarize_results(results: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = Counter(r["allowed"] for r in results)
    return {"allowed": counts.get(True, 0), "blocked": counts.get(False, 0)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run red team prompts")
    parser.add_argument("-o", "--output", type=Path, help="File to write results")
    args = parser.parse_args()

    prompts = load_prompts()
    results = asyncio.run(run_red_team(prompts))
    summary = summarize_results(results)

    output = {"results": results, "summary": summary}
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            yaml.safe_dump(output, f)
    else:
        print(yaml.safe_dump(output))


if __name__ == "__main__":
    main()
