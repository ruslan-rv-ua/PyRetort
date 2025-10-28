import wx
from ...parsers.rss_parser import RSSParser


class AddFeedDialog(wx.Dialog):
    """Dialog for adding new RSS feeds"""
    
    def __init__(self, parent):
        super().__init__(parent, title="Add RSS Feed", size=(400, 200))
        
        # Create controls
        url_label = wx.StaticText(self, label="RSS Feed URL:")
        self.url_text = wx.TextCtrl(self)
        title_label = wx.StaticText(self, label="Feed Title:")
        self.title_text = wx.TextCtrl(self)
        
        # Buttons
        ok_button = wx.Button(self, wx.ID_OK, "Add Feed")
        cancel_button = wx.Button(self, wx.ID_CANCEL, "Cancel")
        
        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        sizer.Add(url_label, 0, wx.ALL, 5)
        sizer.Add(self.url_text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        
        sizer.Add(title_label, 0, wx.ALL, 5)
        sizer.Add(self.title_text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(ok_button, 0, wx.ALL, 5)
        button_sizer.Add(cancel_button, 0, wx.ALL, 5)
        
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        self.SetSizer(sizer)
        
        # Bind events
        self.url_text.Bind(wx.EVT_TEXT, self.on_url_changed)
        
        # Initially disable OK button
        self.FindWindowById(wx.ID_OK).Disable()
    
    def on_url_changed(self, event):
        """Auto-detect feed title when URL changes"""
        url = self.url_text.GetValue().strip()
        if url:
            try:
                parser = RSSParser()
                feed_info = parser.get_feed_info(url)
                title = feed_info.get('title', '')
                if title:
                    self.title_text.SetValue(title)
            except:
                pass  # Silently ignore errors
    
    def get_url(self):
        """Get entered URL"""
        return self.url_text.GetValue().strip()
    
    def get_title(self):
        """Get entered title"""
        return self.title_text.GetValue().strip() or "Untitled Feed"