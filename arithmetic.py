# Copyright (C) 2009, Chris Ball <chris@printf.net>
# Copyright (C) 2009, Benjamin M. Schwartz <bmschwar@fas.harvard.edu>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
"""Arithmetic Activity: A quiz activity for arithmetic."""


import sys, cgitb

cgitb.enable(format="plain")
cgitb.handler = sys.excepthook

import logging
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk
from gi.repository import Pango
import random
from gi.repository import GObject, GLib
import math
import time
import os
import os.path
import hashlib
import dobject.groupthink as groupthink
import dobject.groupthink.gtk_tools as gtk_tools
import dobject.groupthink.sugar_tools as sugar_tools

from gettext import gettext as _
from sugar3.activity import activity
from sugar3 import profile

from sugar3.activity.widgets import ActivityToolbarButton, StopButton
from sugar3.graphics.toolbarbox import ToolbarBox, ToolbarButton


def score_codec(score_or_opaque, pack_or_unpack):
    v = score_or_opaque
    if pack_or_unpack:
        return (v.cumulative_score, v.last_score, v.last_time)
    else:
        return ImmutableScore(cumulative_score=v[0],
                              last_score=v[1],
                              last_time=v[2],)

class ImmutableScore(object):
    """An immutable representation of scores suitable for synchronization
    through Groupthink. The codec function is named score_codec."""

    def __init__(self, old_score = None, cumulative_score=0, last_score=0, last_time=0.0):
        """Immutable objects may be constructed in absolute or relative terms.
        Absolute terms are used when old_score is None.
        Relative terms are used when old_score is an ImmutableScore.
        """
        attrs = [("cumulative_score", lambda a,b: a+b),
                 ("last_score", lambda a,b: b),
                 ("last_time", lambda a,b: b)]
        if old_score is not None:
            for a, u in attrs:
                setattr(self, '_'+a, u(getattr(old_score, a), locals()[a]))
        else:
            for a, u in attrs:
                setattr(self, '_'+a, locals()[a])

    def _get_cumulative_score(self):
        return self._cumulative_score
    cumulative_score = property(_get_cumulative_score)

    def _get_last_score(self):
        return self._last_score
    last_score = property(_get_last_score)

    def _get_last_time(self):
        return self._last_time
    last_time = property(_get_last_time)

class ArithmeticActivity(groupthink.sugar_tools.GroupActivity):
    """Arithmetic Activity as specified in activity.info"""
    DIFFICULTY_EASY     = False
    DIFFICULTY_MEDIUM   = False
    DIFFICULTY_HARD     = False

    def __init__(self, handle):
        super(ArithmeticActivity, self).__init__(handle)

        self._configure_toolbars()

    def _configure_toolbars(self):


        toolbar_box = ToolbarBox()
        toolbar = toolbar_box.toolbar

        activity_button = ActivityToolbarButton(self)
        toolbar_box.toolbar.insert(activity_button, 0)
        activity_button.show()

        self._add_expander(toolbar_box.toolbar)

        toolbar.add(Gtk.SeparatorToolItem())



        stop_button = StopButton(self)
        stop_button.props.accelerator = '<Ctrl><Shift>Q'
        toolbar_box.toolbar.insert(stop_button, -1)
        stop_button.show()

        self.set_toolbar_box(toolbar_box)
        toolbar_box.show()

    def _add_expander(self, toolbar):
        """Insert a toolbar item which will expand to fill the available
        space."""
        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar.insert(separator, -1)
        separator.show()

    def _get_period(self):
        try:
            period = self.cloud.periodentry.get_text()
            period = int(period)
        except:
            period = 10
        return period

    period = property(_get_period)

    def initialize_display(self):
        """Set up the Arithmetic activity."""
        self._logger = logging.getLogger('arithmetic-activity')
        self.starttime = 0
        self.endtime = 0
        self.secondsleft = ""
        self.question = ""
        self.answer = ""
        self.cloud.scoreboard = groupthink.CausalDict(value_translator=score_codec)
        self.scoreboard = self.cloud.scoreboard.__dict__
        self.mynickname = profile.get_nick_name()
        self.scoreboard[self.mynickname] = ImmutableScore()
        self._question_index = 0
        self._puzzle_hashes = set()
        self._puzzle_code = {}
        self._active_mode_hashes = set()

        # Main layout
        vbox = Gtk.VBox()

        # Set a startpoint for a shared seed
        self.cloud.startpoint = groupthink.HighScore(self.timer.time(), 0)

        # Scoreboard
        scorebox = Gtk.VBox()
        self.model = Gtk.TreeStore(GObject.TYPE_STRING, # name
                                   GObject.TYPE_INT,    # last round score
                                   GObject.TYPE_INT,    # total score
                                   GObject.TYPE_FLOAT)  # time for last question
        self.treeview = treeview = Gtk.TreeView(self.model)
        cellrenderer = Gtk.CellRendererText()
        col1 = Gtk.TreeViewColumn(_("Name"), cellrenderer, text=0)
        col2 = Gtk.TreeViewColumn(_("Round score"), cellrenderer, text=1)
        col3 = Gtk.TreeViewColumn(_("Total score"), cellrenderer, text=2)
        col4 = Gtk.TreeViewColumn(_("Time for answering last question"), cellrenderer, text=3)
        treeview.append_column(col1)
        treeview.append_column(col2)
        treeview.append_column(col3)
        treeview.append_column(col4)

        my_score = self.scoreboard[self.mynickname]

        self.olditer = self.model.insert_before(None, None)
        self.model.set_value(self.olditer, 0, self.mynickname)
        self.model.set_value(self.olditer, 1, my_score.last_score)
        self.model.set_value(self.olditer, 2, my_score.cumulative_score)
        self.model.set_value(self.olditer, 3, my_score.last_time)
        treeview.expand_all()
        scorebox.pack_start(treeview, True, True, 0)

        # Horizontal fields
        difficultybox = Gtk.HBox()
        periodbox     = Gtk.HBox()
        toprowbox     = Gtk.HBox()
        modebox       = Gtk.HBox()
        self.inner_modebox = Gtk.HBox()
        questionbox   = Gtk.HBox()
        answerbox     = Gtk.HBox()
        decisionbox   = Gtk.HBox()
        lastroundbox  = Gtk.HBox()
        bottomrowbox  = Gtk.HBox()
        countdownbox  = Gtk.HBox()

        # Labels
        difficultylabel = Gtk.Label(_("Difficulty: "))
        periodlabel     = Gtk.Label(_("Period: "))
        periodunitslabel= Gtk.Label(" sec  ")
        modelabel       = Gtk.Label(_("Puzzles: "))
        questionlabel   = Gtk.Label(_("Question: "))
        answerlabel     = Gtk.Label(_("Answer: "))
        decisionlabel   = Gtk.Label(_("You were: "))
        lastroundlabel  = Gtk.Label(_("Last round: "))
        self.lastanswerlabel = Gtk.Label("")
        staticcountdownlabel = Gtk.Label(_("Time until next question: "))
        self.countdownlabel  = Gtk.Label("")

        # ToggleButtons for difficulty
        self.cloud.easytoggle      = groupthink.gtk_tools.SharedToggleButton("< 10")
        self.cloud.mediumtoggle    = groupthink.gtk_tools.SharedToggleButton("< 20")
        self.cloud.hardtoggle      = groupthink.gtk_tools.SharedToggleButton("< 50")

        self.cloud.easytoggle.set_active(False)
        self.cloud.mediumtoggle.set_active(False)
        self.cloud.hardtoggle.set_active(False)
        self.cloud.easytoggle.connect("toggled", self.easy_cb)
        self.cloud.mediumtoggle.connect("toggled", self.medium_cb)
        self.cloud.hardtoggle.connect("toggled", self.hard_cb)

        # Entry for puzzle period
        self.cloud.periodentry = groupthink.gtk_tools.RecentEntry(max=2)
        self.cloud.periodentry.modify_font(Pango.FontDescription("Mono 14"))
        self.cloud.periodentry.set_text(str(self.period))
        self.cloud.periodentry.set_width_chars(2)
        self.cloud.periodentry.connect("changed", self._period_cb)

        # Puzzle generators
        self.cloud.puzzles         = groupthink.AddOnlySet()
        self.cloud.puzzles.register_listener(self.new_puzzles_cb)

        # Text entry box for question
        self.questionentry = Gtk.TextView()
        self.questionentry.modify_font(Pango.FontDescription("Mono 14"))
        self.questionentry.set_property("editable", False)

        # Text entry box for answer
        self.answerentry = Gtk.Entry(max=50)
        self.answerentry.modify_font(Pango.FontDescription("Sans 14"))
        self.answerentry.connect("activate", self.answer_cb)

        # Whether the user was correct
        self.decisionentry = Gtk.Entry(max=50)
        self.decisionentry.modify_font(Pango.FontDescription("Sans 14"))
        self.decisionentry.set_property("editable", False)

        # Packing
        difficultybox.pack_start(difficultylabel, False, True, 0)
        difficultybox.pack_start(self.cloud.easytoggle, False, True, 0)
        difficultybox.pack_start(self.cloud.mediumtoggle, False, True, 0)
        difficultybox.pack_start(self.cloud.hardtoggle, False, True, 0)

        periodbox.pack_start(periodlabel, False, True, 0)
        periodbox.pack_start(self.cloud.periodentry, False, True, 0)
        periodbox.pack_start(periodunitslabel, False, True, 0)

        toprowbox.pack_start(difficultybox, False, True, 0)
        toprowbox.pack_end(periodbox, False, True, 0)

        questionbox.pack_start(questionlabel, False, True, 0)
        questionbox.pack_start(self.questionentry, True, True, 0)
        modebox.pack_start(modelabel, False, True, 0)
        modebox.pack_start(self.inner_modebox, True, True, 0)
        answerbox.pack_start(answerlabel, False, True, 0)
        answerbox.pack_start(self.answerentry, True, True, 0)
        decisionbox.pack_start(decisionlabel, False, True, 0)
        decisionbox.pack_start(self.decisionentry, True, True, 0)

        lastroundbox.pack_start(lastroundlabel, False, True, 0)
        lastroundbox.pack_start(self.lastanswerlabel, False, True, 0)

        countdownbox.pack_start(staticcountdownlabel, False, True, 0)
        countdownbox.pack_start(self.countdownlabel, False, True, 0)

        bottomrowbox.pack_start(countdownbox, True, True, 0)
        bottomrowbox.pack_end(lastroundbox, True, True, 0)

        vbox.pack_start(toprowbox, False, True, 0)
        vbox.pack_start(modebox, False, True, 0)
        vbox.pack_start(questionbox, False, True, 0)
        vbox.pack_start(answerbox, False, True, 0)
        vbox.pack_start(decisionbox, False, True, 0)
        vbox.pack_start(countdownbox, False, True, 0)
        vbox.pack_start(bottomrowbox, False, True, 0)
        vbox.pack_start(scorebox, True, True, 0)

        # Set defaults for questions.
        self.setup_puzzles()
        self.cloud.easytoggle.set_active(True)

        # Make a new question.
        self.generate_new_question()
        self.start_question()
        self.start_countdown()
        self.answerentry.grab_focus()
        self.lastanswerlabel.set_markup("")
        return vbox

    def when_initiating_sharing(self):
        self.cloud.startpoint.set_value(self.timer.time(), 1)

    def generate_new_question(self):
        # This requires a fairly large comment.
        #
        # There are at least two possible solutions to the problem of
        # trying to show the same questions on every client at (roughly)
        # the same time.  They are:
        #  1)  Share a random seed beforehand and draw questions from it,
        #      so that everyone gets the same questions.  Synchronize
        #      clocks to make sure that people are seeing the same
        #      questions at the same time, and establish that question N
        #      will start at time starttime + (period * N).  This requires a
        #      passable attempt at clock synchronization, but then the
        #      clients can cease communicating with each other (forever!)
        #      and still know what question to pop up when.
        #  2)  Nominate someone to choose the questions, and wait for
        #      messages from that person that tell you what the question
        #      is and when you should start it.  This requires a reliable
        #      network link with relatively low latency, and algorithms
        #      that can avoid races when people leave and rejoin a game.
        #
        # We decided to go for 1), using Groupthink to work out a shared
        # clock, stating that questions start every ten seconds, and
        # using a shared seed -- self.cloud.startpoint -- plus a question
        # index.
        t0 = self.cloud.startpoint.get_value()
        random.seed((t0, self._question_index))

        difficultylist = list()
        if self.DIFFICULTY_EASY:
            difficultylist.append("easy")
        if self.DIFFICULTY_MEDIUM:
            difficultylist.append("medium")
        if self.DIFFICULTY_HARD:
            difficultylist.append("hard")

        # This requires a fairly large comment.
        if len(self._active_mode_hashes) > 0 and len(difficultylist) > 0:
            mode = random.choice(list(self._active_mode_hashes))
            difficulty = random.choice(difficultylist)
            self.question, self.answer = self.generate_problem(mode, difficulty)
        else:
            self.inner_modebox.get_children()[0].set_active(True)
            self.question = self.answer = ""

    def generate_problem(self, mode, difficulty):
        mode_dict = self._puzzle_code[mode]
        get_problem = mode_dict['get_problem']
        return get_problem(self, difficulty)

    def generate_number(self, difficulty, lessthan=0):
        if difficulty == "easy":
            return random.randint(1, lessthan or 9)
        if difficulty == "medium":
            return random.randint(1, lessthan or 19)
        if difficulty == "hard":
            return random.randint(1, lessthan or 50)
        else:
            raise AssertionError

    def solve (self, answer, incorrect=False):
        try:
            answer = int(answer)
        except ValueError:
            self.answerentry.set_text("")
            self.decisionentry.set_text("")
            return

        self.endtime = time.time()
        self.model.set_value(self.olditer, 3, self.endtime - self.starttime)

        if int(answer) == int(self.answer):
            self.answercorrect = True
            self.decisionentry.set_text(_("Correct!"))
            old_score = self.scoreboard[self.mynickname]
            new_score = ImmutableScore(old_score=old_score,
                                       cumulative_score=1,
                                       last_score=1,
                                       last_time=self.endtime - self.starttime,)
            self.scoreboard[self.mynickname] = new_score
        else:
            self.answercorrect = False
            self.decisionentry.set_text(_("Not correct"))

    # Callbacks.
    def _period_cb(self, _):
        try:
            period = self.cloud.periodentry.get_text()
            period = int(period)
            if   period < 1:  self.cloud.periodentry.set_text("10")
            elif period > 99: self.cloud.periodentry.set_text("60")
        except:
            pass

    def answer_cb(self, answer, incorrect=False):
        self.answergiven = True
        self.solve(self.answerentry.get_text())

    def start_countdown(self):
        self.secondsleft = self.period
        GLib.timeout_add(1000, self.onesecond_cb)
        self.countdownlabel.set_markup(' <span size="xx-large">%s</span>s' % self.secondsleft)

    def onesecond_cb(self):
        elapsed_time = self.timer.time() - self.cloud.startpoint.get_value()
        curr_index = int(math.floor(elapsed_time/self.period))
        time_to_next = self.period - (elapsed_time - (self.period*curr_index))
        self.secondsleft = int(math.ceil(time_to_next))
        self.countdownlabel.set_markup(' <span size="xx-large">%s</span>s' % self.secondsleft)
        if curr_index != self._question_index:
            self._question_index = curr_index
            if self.answergiven == False:
                self.solve("")
            self.start_question()
            self.answerentry.set_text("")

        self.model = Gtk.TreeStore(GObject.TYPE_STRING, # name
                                   GObject.TYPE_INT,    # last round score
                                   GObject.TYPE_INT,    # total score
                                   GObject.TYPE_FLOAT)  # time for last question

        for person, score in list(self.scoreboard.items()):
            self.model.append(None, (person, score.last_score, score.cumulative_score, score.last_time))

        self.treeview.set_model(self.model)
        return True

    def start_question(self):
        old_answer = self.answer
        old_question = self.question.replace("\n", "  ")
        old_answergiven = getattr(self, "answergiven", False)
        old_answercorrect = getattr(self, "answercorrect", False)

        self.starttime = time.time()
        self.generate_new_question()
        self.questionentry.get_buffer().set_text(self.question)
        self.answergiven = False
        self.answercorrect = False
        self.answerentry.set_text("")
        self.decisionentry.set_text("")

        if self.cloud.periodentry.get_text() != str(self.secondsleft):
            self.cloud.periodentry.set_text(str(self.period))

        markup = "%s : <span weight=\"bold\" color=\"%s\">%s</span>" % (
            old_question,
            old_answercorrect and "blue" or "black",
            old_answer)
        self.lastanswerlabel.set_markup(markup.strip())


    def easy_cb(self, toggled):
        self.DIFFICULTY_EASY = toggled.get_active()
        self.answerentry.grab_focus()

    def medium_cb(self, toggled):
        self.DIFFICULTY_MEDIUM = toggled.get_active()
        self.answerentry.grab_focus()

    def hard_cb(self, toggled):
        self.DIFFICULTY_HARD = toggled.get_active()
        self.answerentry.grab_focus()

    def puzzle_toggle_cb(self, toggled, puzzle_hash):
        if toggled.get_active():
            self._active_mode_hashes.add(puzzle_hash)
        else:
            self._active_mode_hashes.remove(puzzle_hash)
        if hasattr(self, 'answerentry'):
            self.answerentry.grab_focus()

    def setup_puzzles(self):
        puzzle_names = os.listdir("puzzles")
        puzzle_names.sort()
        for name in puzzle_names:
            if name.endswith(".py"):
                path = os.path.join("puzzles", name)
                with open(path, 'r') as file:
                    text = file.read()
                    self.cloud.puzzles.add(text)
                    self.new_puzzles_cb(set([text]))
        self.start_question()
        self.start_countdown()

    def new_puzzles_cb(self, puzzles):
        for text in puzzles:
            if text.strip() == '':
                continue

            md = hashlib.sha1()
            md.update(text)
            hash = md.digest().encode("hex")

            if hash not in self._puzzle_hashes:
                self._puzzle_hashes.add(hash)

                env_global = {}
                env_local = {}
                exec(text, env_global, env_local)

                togglename = hash + "_toggle"
                self.cloud[togglename] = groupthink.gtk_tools.SharedToggleButton(' ' + env_local['name'] + ' ')
                self.cloud[togglename].set_active(False)
                self.cloud[togglename].connect("toggled", self.puzzle_toggle_cb, hash)
                self.cloud[togglename].sort_key = env_local['sort_key']

                self._puzzle_code[hash] = env_local

                kids = self.inner_modebox.get_children()
                old_size = len(kids)

                for kid in kids:
                    self.inner_modebox.remove(kid)

                kids.append(self.cloud[togglename])

                kids.sort(key=lambda x: x.sort_key)

                for kid in kids:
                    self.inner_modebox.pack_start(kid, False, True, 0)
