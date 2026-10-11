"""WCAG contrast on the actual text tokens; decorative skyline is excluded."""

from math import pow


def luminance(color: str) -> float:
    rgb = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.04045 else pow((c + 0.055) / 1.055, 2.4) for c in rgb]
    return sum(c * weight for c, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True))


def main():
    pairs = [
        ("Body", "#e8e6df", "#080f1c"),
        ("Muted", "#a3adbd", "#0e1829"),
        ("Small labels", "#8996aa", "#080f1c"),
        ("Primary button", "#080f1c", "#f5bb67"),
        ("Links", "#75dce5", "#0e1829"),
        ("Matrix max emphasis", "#e8e6df", "#4a3f31"),
        ("Tooltip", "#e8e6df", "#202e44"),
    ]
    for name, fg, bg in pairs:
        a, b = sorted((luminance(fg), luminance(bg)))
        ratio = (b + 0.05) / (a + 0.05)
        print(f"{name}: {ratio:.2f}:1")
        assert ratio >= 4.5, name


if __name__ == "__main__":
    main()
