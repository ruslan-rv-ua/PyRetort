import wx
import webbrowser
from ...models.article import Article


class ArticlePanel(wx.Panel):
    """Right panel showing articles from selected feed"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.current_feed = None
        self.show_unread_only = False
        
        # Create article list
        self.article_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.article_list.InsertColumn(0, "Title", width=600)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.article_list, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)
        
        # Bind events
        self.article_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_article_activated)
    
    def load_articles(self, feed):
        """Load articles for selected feed"""
        self.current_feed = feed
        
        # Get articles based on filter
        if self.show_unread_only:
            articles = Article.select().where(
                (Article.feed == feed) &
                (Article.is_read == False)
            )
        else:
            articles = Article.select().where(Article.feed == feed)
        
        self.article_list.DeleteAllItems()
        
        for i, article in enumerate(articles):
            index = self.article_list.InsertItem(i, article.title)
            self.article_list.SetItemData(index, article.id)
        
        # Auto-select and focus first item if there are articles
        if articles.count() > 0:
            self.article_list.Focus(0)
            self.article_list.Select(0)
    
    def clear_articles(self):
        """Clear article list"""
        self.article_list.DeleteAllItems()
        self.current_feed = None
    
    def set_view_mode(self, mode):
        """Set view mode: 'all' or 'unread'"""
        self.show_unread_only = (mode == 'unread')
        if self.current_feed:
            self.load_articles(self.current_feed)
    
    def on_article_activated(self, event):
        """Open article in default browser"""
        index = event.GetIndex()
        if index != -1:
            article_id = self.article_list.GetItemData(index)
            selected_article = Article.get_by_id(article_id)
            
            # Mark as read
            selected_article.is_read = True
            selected_article.save()
            
            # Refresh list
            self.load_articles(self.current_feed)
            
            # Open in browser
            webbrowser.open(selected_article.url)
    
    def mark_selected_as_read(self):
        """Mark selected articles as read"""
        index = self.article_list.GetFirstSelected()
        while index != -1:
            article_id = self.article_list.GetItemData(index)
            article = Article.get_by_id(article_id)
            article.is_read = True
            article.save()
            index = self.article_list.GetNextSelected(index)
        
        # Refresh list
        if self.current_feed:
            self.load_articles(self.current_feed)
    
    def mark_selected_as_unread(self):
        """Mark selected articles as unread"""
        index = self.article_list.GetFirstSelected()
        while index != -1:
            article_id = self.article_list.GetItemData(index)
            article = Article.get_by_id(article_id)
            article.is_read = False
            article.save()
            index = self.article_list.GetNextSelected(index)
        
        # Refresh list
        if self.current_feed:
            self.load_articles(self.current_feed)