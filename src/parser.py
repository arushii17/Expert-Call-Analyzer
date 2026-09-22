from pathlib import Path

def read_transcript(file_path):
    text = Path(file_path).read_text(encoding="utf-8")
    return text

def extract_metadata(text):
    lines = text.splitlines()

    expert = lines[0].split("–", 1)[-1].strip()
    role = lines[1].replace("Role:", "").strip()
    market = lines[2].replace("Market:", "").strip()

    return {
        "expert": expert,
        "role": role,
        "market": market
    }
    
def is_timestamp(line):
    parts = line.split(":")

    if len(parts) == 2:
        if parts[0].isdigit() and parts[1].isdigit():
            return True

    return False    

def parse_transcript(file_path):

    text = read_transcript(file_path)

    metadata = extract_metadata(text)

    lines = text.splitlines()

    segments = []

    current_timestamp = None
    
    source_file = Path(file_path).name

    for line in lines:

        line = line.strip()
        
        if not line:
            continue

        if is_timestamp(line):
            current_timestamp = line
            continue

        if current_timestamp and ":" in line:

            speaker, speech = line.split(":", 1)

            segment = {
                "expert": metadata["expert"],
                "role": metadata["role"],
                "market": metadata["market"],
                "source": source_file,
                "timestamp": current_timestamp,
                "speaker": speaker.strip(),
                "text": speech.strip()
            }

            segments.append(segment)

    return segments


def load_all_transcripts(data_dir="data"):

    transcript_files = [
        "Transcript_1_France.txt",
        "Transcript_2_Germany.txt",
        "Transcript_3_UK.txt"
    ]

    all_segments = []

    for filename in transcript_files:

        file_path = Path(data_dir) / filename

        segments = parse_transcript(file_path)

        all_segments.extend(segments)

    return all_segments

if __name__ == "__main__":

    results = load_all_transcripts()

    for segment in results:
        print(segment)

    print("\nTotal segments:", len(results))