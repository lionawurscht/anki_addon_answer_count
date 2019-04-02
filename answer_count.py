#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A simple addon to display the number of answers in parenthesis after the
question.

For this the card needs to have a tag that starts with  `answer_count` or
`answer_count_<split_char>` where <split_char> will be used to split the
answer into answers. Several split chars can be given by adding more tags.
The default split char for splitting the answer.

This addon expects the answer to reside in the field `Back` as is the case for
the `Basic` note type.
"""


# Third Party
from PyQt5 import QtCore, QtGui, QtWidgets

# This Module
import anki
import aqt
from anki.hooks import addHook, wrap
from aqt import mw
from aqt.utils import showInfo

# Default values
ANSWER_COUNT_TAG = "multiple_answers"

SPLIT_CHARS = {"space": " "}

ANSWER_FIELD_NAME = "Back"

DEFAULT_SPLIT_CHAR = ","


# So I'm not pestered with havin to transform stuff to string manually
def show_info(*args):
    if len(args) == 1:
        args = args[0]

    showInfo(str(args))


# The filter that does the actual work


def on_prepare_qa(to_review, card, type_):
    """Gets the question before it is shown and count the answers. Returns an
    altered question as a `str`."""

    qc = mw.col.conf

    answer_count_tag = qc["ac_tag"]
    answer_field_name = qc["ac_answer_field"]
    default_split_char = qc["ac_default_split_char"]

    if type_ not in ["reviewQuestion", "previewQuestion"]:
        return to_review

    # Now we know we're dealing with a question
    question = to_review

    # Get the note
    note = card.note()

    # Get the tags
    tags = note.stringTags().split(" ")

    # Find the split chars
    answer_count_tag_suffixes = [
        tag[len(answer_count_tag) :] for tag in tags if tag.startswith(answer_count_tag)
    ]

    # We are only interested in notes which declared themselves to have
    # multiple answers

    if not answer_count_tag_suffixes:
        return question

    # Actually only get the split char minus the `_`
    answers_split_chars = [suffix[1:] for suffix in answer_count_tag_suffixes if suffix]

    if not answers_split_chars:
        answers_split_chars = [default_split_char]

    # Allow special split chars by checking in `SPLIT_CHARS` whether a
    # replacement value is supplied
    answers_split_chars = [
        SPLIT_CHARS.get(split_char, split_char) for split_char in answers_split_chars
    ]

    # Get the answer
    try:
        answer = note[answer_field_name]
    except KeyError:
        return question

    # We are not interested in newlines
    answer = answer.strip("\n")

    # The loop assumes a list of strings for each iteration ...
    answers = [answer]

    # Repeatedly split the answer by all the split chars

    for split_char in answers_split_chars:
        answers = [answer.split(split_char) for answer in answers]
        answers = [
            answer for answer_group in answers for answer in answer_group if answer
        ]

    # Get the the answer count
    answer_count = len(answers)

    question_lines = question.split("\n")

    # Find the last line with text in it.

    for i, line in enumerate(reversed(question_lines)):
        if line.strip():
            break

    # get the actual index
    i = len(question_lines) - i - 1

    # Add the answer count to the question
    question_lines[i] = f"{question_lines[i]} ({answer_count})"

    # And return a string

    return "\n".join(question_lines)


addHook("prepareQA", on_prepare_qa)
# Preference menu


def ac_preferences_setup_ui(self, Preferences):
    self.ac_tab = QtWidgets.QWidget()
    self.ac_vl = QtWidgets.QGridLayout(self.ac_tab)
    self.ac_vl.setColumnStretch(0, 0)
    self.ac_vl.setColumnStretch(1, 0)
    self.ac_vl.setColumnStretch(2, 0)
    self.ac_vl.setColumnStretch(3, 1)

    row = 0
    general = QtWidgets.QLabel("<b>Answer count settings</b>")
    self.ac_vl.addWidget(general, row, 0, 1, 3)
    row += 1

    ac_tag_label = QtWidgets.QLabel("Answer count tag")
    ac_tag_label.setToolTip(
        "The tag used to find the cards on which to count the answers."
    )
    self.ac_tag_edit = QtWidgets.QLineEdit(self.ac_tab)
    self.ac_vl.addWidget(ac_tag_label, row, 0)
    self.ac_vl.addWidget(self.ac_tag_edit, row, 1)
    row += 1

    ac_answer_field_label = QtWidgets.QLabel("Answer field")
    ac_answer_field_label.setToolTip(
        "The name of the field that the answer should be gotten from."
    )
    self.ac_answer_field_edit = QtWidgets.QLineEdit(self.ac_tab)
    self.ac_vl.addWidget(ac_answer_field_label, row, 0)
    self.ac_vl.addWidget(self.ac_answer_field_edit, row, 1)
    row += 1

    ac_default_split_char_label = QtWidgets.QLabel("Default split character")
    ac_default_split_char_label.setToolTip(
        "The character used to split answers if no other character is supplied through tags. Special value you can use are: {}".format(
            ", ".join(
                "{}={!r}".format(alias, char) for alias, char in SPLIT_CHARS.items()
            )
        )
    )
    self.ac_default_split_char_edit = QtWidgets.QLineEdit(self.ac_tab)
    self.ac_vl.addWidget(ac_default_split_char_label, row, 0)
    self.ac_vl.addWidget(self.ac_default_split_char_edit, row, 1)
    row += 1

    spacer = QtWidgets.QSpacerItem(
        1, 1, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
    )
    self.ac_vl.addItem(spacer, row, 0)

    self.tabWidget.addTab(self.ac_tab, "Answer counts")


def ac_preferences_init(self, mw):
    qc = self.mw.col.conf
    self.form.ac_tag_edit.setText(qc["ac_tag"])
    self.form.ac_answer_field_edit.setText(qc["ac_answer_field"])
    self.form.ac_default_split_char_edit.setText(qc["ac_default_split_char"])


def ac_preferences_accept(self):
    qc = self.mw.col.conf

    qc["ac_tag"] = self.form.ac_tag_edit.text()
    qc["ac_answer_field"] = self.form.ac_answer_field_edit.text()
    qc["ac_default_split_char"] = self.form.ac_default_split_char_edit.text()


aqt.forms.preferences.Ui_Preferences.setupUi = wrap(
    aqt.forms.preferences.Ui_Preferences.setupUi, ac_preferences_setup_ui, pos="after"
)
aqt.preferences.Preferences.__init__ = wrap(
    aqt.preferences.Preferences.__init__, ac_preferences_init, pos="after"
)
aqt.preferences.Preferences.accept = wrap(
    aqt.preferences.Preferences.accept, ac_preferences_accept, pos="before"
)


# Set the default config


def init_conf(self):
    qc = self.conf
    keys = {
        "ac_answer_field": ANSWER_FIELD_NAME,
        "ac_tag": ANSWER_COUNT_TAG,
        "ac_default_split_char": DEFAULT_SPLIT_CHAR,
    }

    for k in keys:
        if k not in qc:
            qc[k] = keys[k]


anki.collection._Collection.load = wrap(
    anki.collection._Collection.load, init_conf, pos="after"
)
