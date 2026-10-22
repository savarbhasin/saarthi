import argparse
import asyncio

from saarthi.domain.phone import normalize_phone
from saarthi.voice.outbound import call_phone


def main() -> None:
    parser = argparse.ArgumentParser(description="Have Saarthi call a phone number")
    parser.add_argument("phone", help="number to call, e.g. 9876543210 or +919876543210")
    args = parser.parse_args()
    execution_id = asyncio.run(call_phone(normalize_phone(args.phone)))
    print(f"call queued: execution {execution_id}")


if __name__ == "__main__":
    main()
