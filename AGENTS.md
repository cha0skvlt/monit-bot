tasks:
  - file: bot.py
    action: rename_command
    from: /remove
    to: /rem
    function: cmd_remove

  - file: bot.py
    action: add_command
    command: /add_admin
    function: cmd_add_admin
    decorators: [with_typing, admin_only]
    description: "Adds a new admin by user ID"

  - file: bot.py
    action: add_command
    command: /rm_admin
    function: cmd_rm_admin
    decorators: [with_typing, admin_only]
    description: "Removes an admin by user ID"

  - file: bot.py
    action: implement_function
    function: cmd_add_admin
    code: |
      user_id = ctx.args[0] if ctx.args else None
      if user_id:
          add_admin(user_id)
          update.message.reply_text(f"✅ Admin {user_id} added.")
      else:
          update.message.reply_text("⚠️ Usage: /add_admin <user_id>")

  - file: bot.py
    action: implement_function
    function: cmd_rm_admin
    code: |
      user_id = ctx.args[0] if ctx.args else None
      if user_id:
          remove_admin(user_id)
          update.message.reply_text(f"❌ Admin {user_id} removed.")
      else:
          update.message.reply_text("⚠️ Usage: /rm_admin <user_id>")
