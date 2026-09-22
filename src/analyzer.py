import os
import json

from dotenv import load_dotenv
from backboard import BackboardClient

from parser import load_all_transcripts


load_dotenv()

api_key = os.getenv("BACKBOARD_API_KEY")

if not api_key:
    raise ValueError("BACKBOARD_API_KEY not found in .env")

segments = load_all_transcripts()


def get_client():
    return BackboardClient(api_key=api_key)


def clean_json(content):
    content = content.strip()

    if content.startswith("```"):
        content = content.replace("```json", "")
        content = content.replace("```", "")
        content = content.strip()

    return json.loads(content)


def get_expert_transcripts():

    transcripts = {}

    for segment in segments:

        if segment["speaker"] == "Interviewer":
            continue

        expert = segment["expert"]

        if expert not in transcripts:
            transcripts[expert] = {
                "market": segment["market"],
                "source": segment["source"],
                "evidence": []
            }

        transcripts[expert]["evidence"].append({
            "timestamp": segment["timestamp"],
            "text": segment["text"]
        })

    return transcripts


async def generate_answer(question, evidence):

    context = ""

    for item in evidence:
        context += f"[{item['timestamp']}] {item['text']}\n"

    prompt = f"""
Question:
{question}

Transcript:
{context}

Answer the question using only this transcript.

Return only valid JSON:

{{
    "answer": "concise answer",
    "timestamps": ["timestamp"]
}}

Rules:
- Use only the transcript.
- Do not use outside knowledge.
- Answer only what the question asks.
- Do not add related information unless necessary.
- Do not infer relationships not explicitly supported.
- Select only timestamps that directly support the answer.
- Use the minimum number of timestamps needed.
- Do not invent timestamps.
- If part of the question is not discussed, clearly say so.
- If there is not enough information, return:
  "answer": "Not enough information in this transcript."
  "timestamps": []
"""

    client = get_client()

    response = await client.send_message(
        prompt,
        system_prompt=(
            "You analyze expert interview transcripts. "
            "Use only the supplied transcript evidence."
        ),
        stream=False
    )

    try:
        return clean_json(response.content)

    except json.JSONDecodeError:
        return {
            "answer": "Could not generate a structured answer.",
            "timestamps": []
        }


def get_exact_quotes(evidence, timestamps):

    quotes = []

    for timestamp in timestamps:

        for item in evidence:

            if item["timestamp"] == timestamp:

                quotes.append({
                    "quote": item["text"],
                    "timestamp": item["timestamp"]
                })

                break

    return quotes


async def analyze_guide_question(question):

    transcripts = get_expert_transcripts()
    results = []

    for expert, data in transcripts.items():

        generated = await generate_answer(
            question,
            data["evidence"]
        )

        quotes = get_exact_quotes(
            data["evidence"],
            generated["timestamps"]
        )

        evidence = []

        for quote in quotes:

            evidence.append({
                "quote": quote["quote"],
                "timestamp": quote["timestamp"],
                "source": data["source"]
            })

        results.append({
            "expert": expert,
            "market": data["market"],
            "answer": generated["answer"],
            "evidence": evidence
        })

    return results


async def ask_transcripts(question):

    all_evidence = []

    for segment in segments:

        if segment["speaker"] == "Interviewer":
            continue

        all_evidence.append({
            "expert": segment["expert"],
            "market": segment["market"],
            "source": segment["source"],
            "timestamp": segment["timestamp"],
            "text": segment["text"]
        })

    context = ""

    for i, item in enumerate(all_evidence):

        context += (
            f"\nEvidence ID: {i}\n"
            f"Expert: {item['expert']}\n"
            f"Market: {item['market']}\n"
            f"Timestamp: {item['timestamp']}\n"
            f"Text: {item['text']}\n"
        )

    prompt = f"""
Question:
{question}

Transcript evidence:
{context}

Answer the user's question using only the transcript evidence above.

Return only valid JSON:

{{
    "answer": "concise analytical answer",
    "evidence_ids": [0]
}}

Rules:
- Use only the supplied transcript evidence.
- Do not use outside knowledge.
- Answer only what the user asks.
- The question may concern one expert, multiple experts, or all experts.
- Consider evidence from every relevant expert before answering.
- Do not include unrelated experts.
- The transcript may express a concept using different wording than the user's question.
- Use clearly equivalent transcript language when supported.
- Do not introduce new facts.
- Do not invent information.
- Do not infer unsupported relationships.
- Select only evidence IDs that directly support the answer.
- Use the minimum evidence needed.
- If experts differ, explain the difference without exaggerating disagreement.
- If the transcripts do not contain the requested information, return:
  "answer": "The provided transcripts do not contain this information."
  "evidence_ids": []
"""

    client = get_client()

    response = await client.send_message(
        prompt,
        system_prompt=(
            "You answer questions about expert interview transcripts. "
            "Use only the supplied evidence."
        ),
        stream=False
    )

    try:
        generated = clean_json(response.content)

    except json.JSONDecodeError:
        return {
            "answer": "Could not generate a structured answer.",
            "evidence": []
        }

    selected_evidence = []

    for evidence_id in generated.get("evidence_ids", []):

        if (
            isinstance(evidence_id, int)
            and 0 <= evidence_id < len(all_evidence)
        ):
            selected_evidence.append(
                all_evidence[evidence_id]
            )

    return {
        "answer": generated.get(
            "answer",
            "Could not generate an answer."
        ),
        "evidence": selected_evidence
    }


async def analyze_cross_call():

    transcripts = get_expert_transcripts()
    context = ""

    for expert, data in transcripts.items():

        context += f"\n--- {expert} | {data['market']} ---\n"

        for item in data["evidence"]:
            context += f"[{item['timestamp']}] {item['text']}\n"

    prompt = f"""
Analyze the three expert interviews below.

{context}

Identify:
1. The most important themes shared by all three experts.
2. The most important differences in their views or emphasis.

Return only valid JSON:

{{
    "common_themes": [
        {{
            "theme": "short theme name",
            "summary": "one concise sentence explaining what all three experts have in common"
        }}
    ],
    "differences": [
        {{
            "topic": "short topic name",
            "france": "concise France view",
            "germany": "concise Germany view",
            "uk": "concise UK view",
            "difference": "one concise explanation of the key difference"
        }}
    ]
}}

Rules:
- Use only the supplied transcripts.
- Do not use outside knowledge.
- Do not invent information.
- A common theme must be explicitly supported by all three experts.
- Return only the 3 most important common themes.
- Return only the 3 most important differences.
- Keep every description concise.
- Do not repeat the same finding in multiple sections.
- A difference in emphasis is not automatically a disagreement.
- Do not claim experts disagree unless their views actually conflict.
- Do not infer a position from missing information.
- Focus on adoption, barriers, economics, training,
  clinical outcomes, growth and purchasing.
"""

    client = get_client()

    response = await client.send_message(
        prompt,
        system_prompt=(
            "You compare expert interview transcripts. "
            "Use only supplied evidence and do not exaggerate disagreements."
        ),
        stream=False
    )

    try:
        return clean_json(response.content)

    except json.JSONDecodeError:
        return {
            "common_themes": [],
            "differences": []
        }