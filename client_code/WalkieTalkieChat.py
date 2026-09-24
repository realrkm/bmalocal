from ._anvil_designer import WalkieTalkieChatTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.js
from anvil.js import window


class WalkieTalkieChat(WalkieTalkieChatTemplate):
    def __init__(self, user_profile=None, on_close=None, **properties):
        self.init_components(**properties)
        self.on_close = on_close
        self.user_profile = user_profile

        # Hook close button handler
        def handle_close(*args):
            if callable(self.on_close):
                self.on_close()

        window.onWtChatClose = handle_close

        # Hook refresh handler called when refresh/reload icon is clicked
        def handle_refresh(*args):
            self.refresh_from_server()

        window.onWtChatRefresh = handle_refresh

        if self.user_profile:
            self.set_profile(self.user_profile)
        else:
            self.load_profile()

    def load_profile(self):
        try:
            user = anvil.users.get_user()
            if user:
                email = user["email"] if "email" in user else ""
                role_id = user["role_id"] if "role_id" in user else None
                if email:
                    prof = {
                        "email": email,
                        "name": email.split("@")[0],
                        "role_name": "Admin" if role_id == 1 else "Staff",
                    }
                    self.set_profile(prof)
                    return
        except Exception:
            pass

        try:
            prof = anvil.server.call_s("get_chat_user_profile")
            if prof:
                self.set_profile(prof)
        except Exception:
            pass

    def set_profile(self, profile):
        self.user_profile = profile
        try:
            anvil.js.call("setWtCurrentUser", profile)
        except Exception as e:
            print("Error passing user profile to Walkie Talkie chat:", e)

    def refresh_from_server(self):
        """Fetch latest messages directly from MySQL and update the chat UI."""
        try:
            self.load_profile()
            history = anvil.server.call_s("get_chat_history", 100)
            if history is not None:
                anvil.js.call("renderWtHistoryFromAnvil", history)
        except Exception as e:
            print("Chat refresh error:", e)
