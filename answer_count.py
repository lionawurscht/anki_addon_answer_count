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
import aqt.deckconf
from anki.hooks import addHook, wrap
from aqt import mw
from aqt.utils import showInfo

# Default values
AC_TAG = "multiple_answers"

AC_QUESTION_FIELD = "Front"

AC_ANSWER_FIELD = "Back"

AC_DEFAULT_SPLIT_CHAR = ","

DEFAULT_CONF = {
    "ac_question_field": AC_QUESTION_FIELD,
    "ac_answer_field": AC_ANSWER_FIELD,
    "ac_tag": AC_TAG,
    "ac_default_split_char": AC_DEFAULT_SPLIT_CHAR,
}

SPLIT_CHARS = {"space": " "}

# So I'm not pestered with havin to transform stuff to string manually
def show_info(*args):
    if len(args) == 1:
        args = args[0]

    showInfo(str(args))


# The filter that does the actual work


def on_munge_fields(fields, model, data, self):
    deckconf = self.decks.confForDid(data[3])
    qc = mw.col.conf
    conf = {}

    keys = DEFAULT_CONF.keys()

    for key in keys:
        conf[key] = deckconf.get(key, qc[key])

    answer_count_tag = conf["ac_tag"]
    answer_field = conf["ac_answer_field"]
    question_field = conf["ac_question_field"]
    default_split_char = conf["ac_default_split_char"]

    # show_info(fields)
    answer = fields[answer_field]

    # Now we know we're dealing with a question
    question = fields[question_field]

    # Get the tags
    tags = fields["Tags"].split(" ")

    # Find the split chars
    answer_count_tag_suffixes = [
        tag[len(answer_count_tag) :] for tag in tags if tag.startswith(answer_count_tag)
    ]

    # We are only interested in notes which declared themselves to have
    # multiple answers

    if not answer_count_tag_suffixes:
        return fields

    # Actually only get the split char minus the `_`
    answers_split_chars = [suffix[1:] for suffix in answer_count_tag_suffixes if suffix]

    if not answers_split_chars:
        answers_split_chars = [default_split_char]

    # Allow special split chars by checking in `SPLIT_CHARS` whether a
    # replacement value is supplied
    answers_split_chars = [
        SPLIT_CHARS.get(split_char, split_char) for split_char in answers_split_chars
    ]

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

    # Add the answer count to the question
    question = f"{question} ({answer_count})"

    fields[question_field] = question
    # And return a string

    return fields


addHook("mungeFields", on_munge_fields)

# Preference menu


class OptionComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.has_changed = False
        self.activated.connect(self.changed)

    def changed(self, *__):
        self.has_changed = True


class OptionLineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.has_changed = False
        self.textChanged.connect(self.changed)

    def changed(self, *__):
        self.has_changed = True


def get_field_names(mw):
    model_manager = mw.col.models
    models = model_manager.all()
    field_names = [model_manager.fieldNames(m) for m in models]
    # Flatten the list and make sure every name only occurs once
    field_names = set(
        [
            field_name
            for field_name_group in field_names
            for field_name in field_name_group
        ]
    )

    return field_names


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
    self.ac_tag_edit = OptionLineEdit(self.ac_tab)
    self.ac_vl.addWidget(ac_tag_label, row, 0)
    self.ac_vl.addWidget(self.ac_tag_edit, row, 1)
    row += 1

    ac_question_field_label = QtWidgets.QLabel("Question field")
    ac_question_field_label.setToolTip(
        "The name of the field that the question should be gotten from."
    )
    self.ac_question_field_combo = OptionComboBox(self.ac_tab)
    self.ac_vl.addWidget(ac_question_field_label, row, 0)
    self.ac_vl.addWidget(self.ac_question_field_combo, row, 1)
    row += 1

    ac_answer_field_label = QtWidgets.QLabel("Answer field")
    ac_answer_field_label.setToolTip(
        "The name of the field that the answer should be gotten from."
    )
    self.ac_answer_field_combo = OptionComboBox(self.ac_tab)
    self.ac_vl.addWidget(ac_answer_field_label, row, 0)
    self.ac_vl.addWidget(self.ac_answer_field_combo, row, 1)
    row += 1

    ac_default_split_char_label = QtWidgets.QLabel("Default split character")
    ac_default_split_char_label.setToolTip(
        "The character used to split answers if no other character is supplied through tags. Special value you can use are: {}".format(
            ", ".join(
                "{}={!r}".format(alias, char) for alias, char in SPLIT_CHARS.items()
            )
        )
    )
    self.ac_default_split_char_edit = OptionLineEdit(self.ac_tab)
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
    field_names = get_field_names(self.mw)

    self.form.ac_tag_edit.setText(qc["ac_tag"])

    self.form.ac_question_field_combo.clear()
    self.form.ac_question_field_combo.addItems(field_names)
    self.form.ac_question_field_combo.setCurrentText(qc["ac_question_field"])

    self.form.ac_answer_field_combo.clear()
    self.form.ac_answer_field_combo.addItems(field_names)
    self.form.ac_answer_field_combo.setCurrentText(qc["ac_answer_field"])

    self.form.ac_default_split_char_edit.setText(qc["ac_default_split_char"])


def ac_preferences_accept(self):
    qc = self.mw.col.conf

    qc["ac_tag"] = self.form.ac_tag_edit.text()

    qc["ac_question_field"] = self.form.ac_question_field_combo.currentText()
    qc["ac_answer_field"] = self.form.ac_answer_field_combo.currentText()

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


# deck menu stuff


def save_to_deckconf(self, key, getter):
    deckconf = self.conf

    def _save_to_deckconf(i):
        deckconf[key] = getter()

    return _save_to_deckconf


def ac_dconf_load(self):
    keys = DEFAULT_CONF.keys()

    qc = self.mw.col.conf
    deckconf = self.conf

    conf = {}

    for key in keys:
        conf[key] = deckconf.get(key, qc[key])

    field_names = get_field_names(self.mw)

    self.form.ac_tag_edit.setText(conf["ac_tag"])

    self.form.ac_question_field_combo.clear()
    self.form.ac_question_field_combo.addItems(field_names)
    self.form.ac_question_field_combo.setCurrentText(conf["ac_question_field"])

    self.form.ac_answer_field_combo.clear()
    self.form.ac_answer_field_combo.addItems(field_names)
    self.form.ac_answer_field_combo.setCurrentText(conf["ac_answer_field"])

    self.form.ac_default_split_char_edit.setText(conf["ac_default_split_char"])


def ac_dconf_save(self):
    qc = self.mw.col.conf
    deckconf = self.conf

    if self.form.ac_question_field_combo.has_changed:
        deckconf["ac_question_field"] = self.form.ac_question_field_combo.currentText()

    if self.form.ac_answer_field_combo.has_changed:
        deckconf["ac_answer_field"] = self.form.ac_answer_field_combo.currentText()

    if self.form.ac_default_split_char_edit.has_changed:
        deckconf["ac_default_split_char"] = self.form.ac_default_split_char_edit.text()

    if self.form.ac_tag_edit.has_changed:
        deckconf["ac_tag"] = self.form.ac_tag_edit.text()


aqt.forms.dconf.Ui_Dialog.setupUi = wrap(
    aqt.forms.dconf.Ui_Dialog.setupUi, ac_preferences_setup_ui, pos="after"
)
aqt.deckconf.DeckConf.loadConf = wrap(
    aqt.deckconf.DeckConf.loadConf, ac_dconf_load, pos="after"
)
aqt.deckconf.DeckConf.saveConf = wrap(
    aqt.deckconf.DeckConf.saveConf, ac_dconf_save, pos="before"
)

# Set the default config


def init_conf(self):
    qc = self.conf
    keys = DEFAULT_CONF

    for k in keys:
        if k not in qc:
            qc[k] = keys[k]


anki.collection._Collection.load = wrap(
    anki.collection._Collection.load, init_conf, pos="after"
)
