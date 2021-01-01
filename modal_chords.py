import subprocess
import numpy as np
import scipy.special

notes = ["c", "cs", "d", "ef", "e", "f", "fs", "g", "af", "a", "bf", "b"]

LILYPOND_TEMPLATE = r"""
\language "english"
\pointAndClickOff
#(set-default-paper-size "letter")

\header {
    title = "{{title}}"
    tagline = ##f
}

\paper {
    indent = 0
}

\markup \tiny {
    note + accidental = closest 12ET; with 50-cent arrows = closest 24EDO; signed number = cent deviation from 12ET
}

\score {
    \new Staff {
        \cadenzaOn
        \override TextScript.self-alignment-X = #CENTER
        \override Accidental.stencil = #ly:text-interface::print

        {{music}}
    }

    \layout {
        \context {
            \Staff
            \omit TimeSignature
            \accidentalStyle dodecaphonic
        }
    }
}
"""


def get_note_info(frequency, tag=""):
    semitones = np.log(frequency) / np.log(2) * 12
    semitones_12et = int(round(semitones))
    pitch_class_12et = semitones_12et % 12
    octave = semitones_12et // 12 - 1
    arrow = int(np.sign(round(semitones * 2) * 0.5 - semitones_12et))
    quarter_tones = semitones_12et + arrow * 0.5
    cent_deviation_from_24edo = int(round((semitones - semitones_12et) * 100))

    lilypond_octave = "'" * octave + "," * -octave
    lilypond_note_name = notes[pitch_class_12et] + lilypond_octave
    note_string = lilypond_note_name + {-1: "v", 0: "", 1: "^"}[arrow] + f" {cent_deviation_from_24edo:+}c"

    lilypond_string = []

    glyph_name = "accidentals"
    if len(notes[pitch_class_12et]) == 1:
        glyph_name += ".natural"
    elif notes[pitch_class_12et][1] == "f":
        glyph_name += ".flat"
    elif notes[pitch_class_12et][1] == "s":
        glyph_name += ".sharp"
    if arrow == 1:
        glyph_name += ".arrowup"
    elif arrow == -1:
        glyph_name += ".arrowdown"

    if octave < 1:
        lilypond_string.append(r"\clef bass")
    else:
        lilypond_string.append(r"\clef treble")

    lilypond_string.append(rf'\once \override Accidental.text = \markup {{ \musicglyph "{glyph_name}" }}')
    lilypond_string.append(rf'<>^\markup \small "{cent_deviation_from_24edo:+}"')
    lilypond_string.append(rf'<>_\markup \small "{tag}"')
    lilypond_string.append(f"{lilypond_note_name}1")

    return "\n".join(lilypond_string)


def render_lilypond(title, modes, out_stem):
    music = []
    for row in modes:
        for frequency, mode_label in row:
            music.append(get_note_info(frequency, mode_label))
        music.append(r'\bar "" \break')
        music.append("\n")

    lilypond_document = (
        LILYPOND_TEMPLATE
            .replace("{{music}}", " ".join(music))
            .replace("{{title}}", title)
    )

    subprocess.run(
        ["lilypond", f"--output={out_stem}", "-"],
        check=True,
        input=lilypond_document,
        encoding="utf-8",
    )

# See Berg & Stork, the Physics of Sound

# Circular modes = nodes are circles
circular_modes = 16
# Radial modes = nodes are wheel-shaped
radial_modes = 10

# J[a, b] = frequency of mode a, b+1
J = np.vstack([scipy.special.jn_zeros(n, circular_modes) for n in range(radial_modes)])
J = J / J[0, 0]

circular_membrane_modes = []
for m in range(radial_modes):
    row = []
    for n in range(circular_modes):
        frequency = J[m, n]
        mode_label = f"{m},{n + 1}"
        row.append((frequency, mode_label))
    circular_membrane_modes.append(row)

render_lilypond("Modes of a Circular Membrane", circular_membrane_modes, "circular_membrane")