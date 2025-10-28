import wx
from .panels.feed_panel import FeedPanel
from .panels.article_panel import ArticlePanel
from .menus.main_menu import create_menu_bar


class MainFrame(wx.Frame):
    """Main application window"""
    
    def __init__(self):
        super().__init__(None, title="Simple RSS", size=(1000, 700))
        
        # Create menu bar
        self.SetMenuBar(create_menu_bar(self))
        
        # Create main panel with sizer
        main_panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Create feed and article panels
        self.feed_panel = FeedPanel(main_panel)
        self.article_panel = ArticlePanel(main_panel)
        
        # Add panels to sizer
        main_sizer.Add(self.feed_panel, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.article_panel, 2, wx.EXPAND | wx.ALL, 5)
        
        main_panel.SetSizer(main_sizer)
        
        # Bind events
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
        # Initialize panels
        self.feed_panel.load_feeds()
    
    def on_close(self, event):
        """Handle application close"""
        self.Destroy()