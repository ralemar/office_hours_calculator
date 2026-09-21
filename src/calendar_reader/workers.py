def parse_workers(text: str) -> list[str]:
    workers, seen = [], set()
    for line in text.splitlines():
        name = line.strip()
        if name and name not in seen:
            seen.add(name)
            workers.append(name)
    return workers
