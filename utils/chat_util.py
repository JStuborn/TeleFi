from re import findall, match as re_match, search

def extract_channel_links(text):
    if not text or not isinstance(text, str):
        return []
    pattern = r't\.me/(?:joinchat/)?[a-zA-Z0-9_-]+'
    return findall(pattern, text)

def clean_link(link):
    if not link or not isinstance(link, str):
        return None
    
    link = link.split(')')[0].strip()
    
    if re_match(r'^[a-zA-Z0-9_]{5,}$', link):
        return link
    
    match_obj = search(r't\.me/(?:joinchat/)?([a-zA-Z0-9_-]+)', link)
    if match_obj:
        username_or_hash = match_obj.group(1)
        
        if 'joinchat' in link:
            return f'https://t.me/joinchat/{username_or_hash}'
        
        return username_or_hash
    
    return None
