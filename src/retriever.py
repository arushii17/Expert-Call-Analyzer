from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from parser import load_all_transcripts


model = SentenceTransformer("all-MiniLM-L6-v2")

segments = load_all_transcripts()

chunks = []
previous_question = ""

for segment in segments:

    if segment["speaker"] == "Interviewer":
        previous_question = segment["text"]

    else:

        chunk = {
            "expert": segment["expert"],
            "role": segment["role"],
            "market": segment["market"],
            "source": segment["source"],
            "timestamp": segment["timestamp"],
            "text": segment["text"],
            "interview_question": previous_question,
            "search_text": previous_question + " " + segment["text"]
        }
        chunks.append(chunk)

search_texts = []

for chunk in chunks:
    search_texts.append(chunk["search_text"])


chunk_embeddings = model.encode(search_texts)


def search_transcripts(question, top_k=8):

    question_embedding = model.encode([question])

    similarities = cosine_similarity(
        question_embedding,
        chunk_embeddings
    )[0]

    results = []

    for i in range(len(chunks)):

        result = {
            "expert": chunks[i]["expert"],
            "role": chunks[i]["role"],
            "market": chunks[i]["market"],
            "source": chunks[i]["source"],
            "timestamp": chunks[i]["timestamp"],
            "text": chunks[i]["text"],
            "score": float(similarities[i]),
            "interview_question": chunks[i]["interview_question"],
        }

        results.append(result)

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:top_k]


if __name__ == "__main__":

    question = "What is the typical hospital decision-making timeline for purchasing a new robotic system?"

    results = search_transcripts(question)

    print("\nQUESTION:")
    print(question)

    print("\nRESULTS:\n")

    for result in results:

        print(
            result["market"],
            "|",
            result["timestamp"],
            "| Score:",
            round(result["score"], 3)
        )

        print(result["text"])
        print("-" * 70)