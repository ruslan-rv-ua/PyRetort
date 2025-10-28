import sys
import wx


def check_windows_platform():
    """Check if running on Windows and exit if not"""
    if sys.platform != 'win32':
        wx.MessageBox("Simple RSS is a Windows-only application.", 
                     "Platform Error", wx.OK | wx.ICON_ERROR)
        sys.exit(1)