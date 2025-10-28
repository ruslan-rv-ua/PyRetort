import wx
from ...models.feed import Feed
from ...parsers.rss_parser import RSSParser
from ..dialogs.add_feed_dialog import AddFeedDialog


class FeedPanel(wx.Panel):
    """Left panel showing RSS feeds"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.feed_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.feed_list.InsertColumn(0, "Title", width=300)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.feed_list, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)
        
        # Bind events
        self.feed_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_feed_selected)
    
    def load_feeds(self):
        """Load all feeds from database"""
        feeds = Feed.select()
        self.feed_list.DeleteAllItems()
        
        for i, feed in enumerate(feeds):
            index = self.feed_list.InsertItem(i, feed.title)
            self.feed_list.SetItemData(index, feed.id)
        
        # Auto-select and focus first feed if there are feeds
        if feeds.count() > 0:
            self.feed_list.Focus(0)
            self.feed_list.Select(0)
            # Trigger the selection event to load articles
            event = wx.ListEvent(wx.wxEVT_LIST_ITEM_SELECTED, self.feed_list.GetId())
            event.SetIndex(0)
            self.GetEventHandler().ProcessEvent(event)
    
    def on_feed_selected(self, event):
        """Handle feed selection"""
        index = event.GetIndex()
        if index != -1:
            feed_id = self.feed_list.GetItemData(index)
            selected_feed = Feed.get_by_id(feed_id)
            
            # Get parent frame and update article panel
            frame = self.GetParent().GetParent()
            frame.article_panel.load_articles(selected_feed)
    
    def add_feed(self):
        """Add new RSS feed"""
        dialog = AddFeedDialog(self)
        if dialog.ShowModal() == wx.ID_OK:
            url = dialog.get_url()
            title = dialog.get_title()
            
            try:
                # Create feed in database
                feed = Feed.create(title=title, url=url)
                
                # Parse feed and add articles
                parser = RSSParser()
                parser.add_articles_from_feed(feed)
                
                # Refresh feed list
                self.load_feeds()
                
                wx.MessageBox("Feed added successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f"Failed to add feed: {e}", "Error", wx.OK | wx.ICON_ERROR)
        
        dialog.Destroy()
    
    def remove_feed(self):
        """Remove selected feed"""
        index = self.feed_list.GetFirstSelected()
        if index != -1:
            feed_id = self.feed_list.GetItemData(index)
            selected_feed = Feed.get_by_id(feed_id)
            
            if wx.MessageBox(f"Remove feed '{selected_feed.title}'?", "Confirm",
                           wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
                # Delete feed and its articles
                selected_feed.delete_instance(recursive=True)
                self.load_feeds()
                
                # Clear article panel
                frame = self.GetParent().GetParent()
                frame.article_panel.clear_articles()
    
    def refresh_feed(self):
        """Refresh selected feed"""
        index = self.feed_list.GetFirstSelected()
        if index != -1:
            feed_id = self.feed_list.GetItemData(index)
            selected_feed = Feed.get_by_id(feed_id)
            
            try:
                parser = RSSParser()
                parser.add_articles_from_feed(selected_feed)
                
                # Refresh article panel
                frame = self.GetParent().GetParent()
                frame.article_panel.load_articles(selected_feed)
            except Exception as e:
                wx.MessageBox(f"Failed to refresh feed: {e}", "Error", wx.OK | wx.ICON_ERROR)