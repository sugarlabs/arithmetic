from dobject.groupthink import sugar_tools, gtk_tools
import sugar3
from gi.repository import Gtk


class SharedTextDemoActivity(sugar_tools.GroupActivity):
    def initialize_display(self):
        self.cloud.textview = gtk_tools.SharedTextView()
        self.cloud.textview.props.wrap_mode = Gtk.WrapMode.WORD
        return self.cloud.textview
