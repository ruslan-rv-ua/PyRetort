def main() -> None:
    """Main entry point for Simple RSS application"""
    from .main import SimpleRSSApp
    
    app = SimpleRSSApp()
    app.MainLoop()
