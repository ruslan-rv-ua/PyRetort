import wx
from .database import initialize_database
from .gui.main_frame import MainFrame
from .utils.platform import check_windows_platform


class SimpleRSSApp(wx.App):
    """Main application class"""
    
    def OnInit(self):
        # Check Windows platform
        check_windows_platform()
        
        # Initialize database
        initialize_database()
        
        # Create and show main frame
        self.frame = MainFrame()
        self.frame.Show()
        
        return True