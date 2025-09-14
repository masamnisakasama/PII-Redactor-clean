import re

# 正規キー集合（既存の TEXT_POLICIES と合わせて増やしてOK）
CANON = {
    "face","email","phone","address","id","name","amount","date",
    "plate","nationalid","zipcode","creditcard","ssn"
}

# よくある日本語/英語の同義語マップ（必要に応じて拡張）
SYN = {
    r"(顔|face)": "face",
    r"(名前|氏名|name)": "name",
    r"(メール|e[- ]?mail|メアド)": "email",
    r"(電話|携帯|phone)": "phone",
    r"(住所|address)": "address",
    r"(日付|date)": "date",
    r"(金額|amount|合計|total)": "amount",
    r"(郵便番号|zip|zipcode)": "zipcode",
    r"(クレジット|クレカ|credit)": "creditcard",
    r"(ナンバー|車両番号|plate|license)": "plate",
    r"(個人番号|マイナンバー|national)": "nationalid",
    r"(社会保障|ssn)": "ssn",
    r"(ID|識別子|identifier)": "id",
}

def nl_to_policy(nl: str) -> str:
    nl = (nl or "").lower()
    hits = set()
    for pat, key in SYN.items():
        if re.search(pat, nl, flags=re.IGNORECASE):
            if key in CANON:
                hits.add(key)
    # “全部/個人情報” のような曖昧語 → よく使う既定セット
    if not hits and re.search(r"(全部|すべて|個人情報|pii)", nl):
        hits.update({"face","name","email","phone","address"})
    return ",".join(sorted(hits))
