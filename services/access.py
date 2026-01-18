def is_admin(uid, admins): return uid in admins
def check_force_join(bot, ch, uid):
    try:
        m=bot.get_chat_member(ch,uid)
        return m.status in ("member","administrator","creator")
    except: return False
