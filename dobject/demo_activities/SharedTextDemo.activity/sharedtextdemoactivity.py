from groupthink import sugar_tools, gtk_tools
import sugar
import gtk

class SharedTextDemoActivity(sugar_tools.GroupActivity):
    def initialize_display(self):
        self.cloud.textview = gtk_tools.SharedTextView()
        self.cloud.textview.props.wrap_mode = gtk.WRAP_WORD
        return self.cloud.textview
