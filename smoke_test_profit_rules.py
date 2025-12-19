"""Smoke test for profit-rule percentage coercion.

Runs without an OpenAI key; it only imports helpers.
"""

from intelligent_agents import _coerce_percentage


def main() -> None:
    cases = [
        (None, 30),
        ("30", 30),
        (30, 30),
        (0.3, 30),  # fraction -> 30%
        ("0.8", 80),  # fraction string -> 80%
        ("bad", 30),
        (-1, 30),
        (150, 30),
    ]

    for value, default in cases:
        coerced = _coerce_percentage(value, default=default)
        print(f"value={value!r:>6} default={default:>3} -> {coerced:>6.2f}")


if __name__ == "__main__":
    main()
