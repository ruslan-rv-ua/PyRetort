import wx


def create_menu_bar(frame):
    """Create main menu bar with keyboard shortcuts"""
    menu_bar = wx.MenuBar()
    
    # File menu
    file_menu = wx.Menu()
    exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tAlt+F4", "Exit application")
    frame.Bind(wx.EVT_MENU, lambda e: frame.Close(), exit_item)
    
    # Feed menu
    feed_menu = wx.Menu()
    add_feed_item = feed_menu.Append(wx.ID_ADD, "&Add Feed...\tCtrl+A", "Add new RSS feed")
    remove_feed_item = feed_menu.Append(wx.ID_DELETE, "&Remove Feed\tDelete", "Remove selected feed")
    feed_menu.AppendSeparator()
    refresh_item = feed_menu.Append(wx.ID_REFRESH, "&Refresh\tF5", "Refresh selected feed")
    
    frame.Bind(wx.EVT_MENU, lambda e: frame.feed_panel.add_feed(), add_feed_item)
    frame.Bind(wx.EVT_MENU, lambda e: frame.feed_panel.remove_feed(), remove_feed_item)
    frame.Bind(wx.EVT_MENU, lambda e: frame.feed_panel.refresh_feed(), refresh_item)
    
    # View menu
    view_menu = wx.Menu()
    view_all_item = view_menu.Append(wx.ID_ANY, "&All Articles\tCtrl+1", "Show all articles", kind=wx.ITEM_RADIO)
    view_unread_item = view_menu.Append(wx.ID_ANY, "&Unread Articles\tCtrl+2", "Show unread articles only", kind=wx.ITEM_RADIO)
    view_menu.Check(view_all_item.GetId(), True)  # Default to "All"
    
    frame.Bind(wx.EVT_MENU, lambda e: frame.article_panel.set_view_mode('all'), view_all_item)
    frame.Bind(wx.EVT_MENU, lambda e: frame.article_panel.set_view_mode('unread'), view_unread_item)
    
    # Article menu
    article_menu = wx.Menu()
    mark_read_item = article_menu.Append(wx.ID_ANY, "Mark as &Read\tCtrl+R", "Mark selected articles as read")
    mark_unread_item = article_menu.Append(wx.ID_ANY, "Mark as &Unread\tCtrl+U", "Mark selected articles as unread")
    
    frame.Bind(wx.EVT_MENU, lambda e: frame.article_panel.mark_selected_as_read(), mark_read_item)
    frame.Bind(wx.EVT_MENU, lambda e: frame.article_panel.mark_selected_as_unread(), mark_unread_item)
    
    # Help menu
    help_menu = wx.Menu()
    about_item = help_menu.Append(wx.ID_ABOUT, "&About", "About Simple RSS")
    frame.Bind(wx.EVT_MENU, lambda e: wx.MessageBox("Simple RSS Reader\n\nA simple RSS reader for Windows\n\nThis application was created using AI exclusively with vibe coding in 1.5 hours",
                                                  "About", wx.OK | wx.ICON_INFORMATION), about_item)
    
    menu_bar.Append(file_menu, "&File")
    menu_bar.Append(feed_menu, "&Feed")
    menu_bar.Append(view_menu, "&View")
    menu_bar.Append(article_menu, "&Article")
    menu_bar.Append(help_menu, "&Help")
    
    return menu_bar