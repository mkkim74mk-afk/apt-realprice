#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
국토부 아파트 실거래(매매/전세) 자동 수집 → data.json
- 기준: 실행하는 날의 직전 2개월(계약년월)
- 지역: 서울 강남구(11680) 대치동
- 단지: 래미안대치팰리스 / 대치르엘 / 동부센트레빌 / 대치아이파크
환경변수 MOLIT_KEY 에 공공데이터포털 '일반 인증키(Decoding)' 를 넣어 실행.
키가 없으면 샘플(예시) 데이터를 생성합니다.
"""
import os, json, datetime, sys
import xml.etree.ElementTree as ET
import urllib.request, urllib.parse

KEY = os.environ.get("MOLIT_KEY", "").strip()
LAWD_CD = "11680"          # 강남구 법정동코드 앞 5자리
DONG = "대치동"            # 동 필터
EFF = 0.74                 # 전용률 가정(평형 추정)

TARGETS = [
    {"id": "rmadp",  "name": "래미안대치팰리스", "keys": ["래미안대치팰리스"], "built": "2015"},
    {"id": "reelle", "name": "대치르엘",        "keys": ["대치르엘"],        "built": "2023"},
    {"id": "dongbu", "name": "동부센트레빌",      "keys": ["동부센트레빌"],      "built": "2005"},
    {"id": "ipark",  "name": "대치아이파크",      "keys": ["대치아이파크"],      "built": "2008"},
]

TRADE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
RENT_URL  = "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"


def norm(s):
    return (s or "").replace(" ", "").lower()


def prev_two_months(ref=None):
    ref = ref or datetime.date.today()
    out = []
    for k in (2, 1):  # [더 이른 달, 더 최근 달]
        mm, yy = ref.month - k, ref.year
        while mm <= 0:
            mm += 12; yy -= 1
        out.append(f"{yy}{mm:02d}")
    return out


def g(item, *tags):
    for t in tags:
        e = item.find(t)
        if e is not None and e.text:
            return e.text.strip()
    return ""


def fetch(url, ymd):
    """한 달치 전체 페이지 수집. item dict 리스트 반환."""
    rows, page = [], 1
    while True:
        qs = urllib.parse.urlencode({
            "serviceKey": KEY, "LAWD_CD": LAWD_CD, "DEAL_YMD": ymd,
            "pageNo": page, "numOfRows": 1000,
        })
        req = urllib.request.Request(f"{url}?{qs}", headers={"User-Agent": "molit-auto/1.0"})
        with urllib.request.urlopen(req, timeout=40) as r:
            raw = r.read().decode("utf-8", "replace")
        root = ET.fromstring(raw)

        code = root.findtext(".//resultCode") or root.findtext(".//returnReasonCode")
        if code and code not in ("00", "000"):
            msg = root.findtext(".//resultMsg") or root.findtext(".//returnAuthMsg") or raw[:200]
            raise RuntimeError(f"API 오류({code}): {msg}")

        items = root.findall(".//item")
        if not items:
            break
        rows.extend(items)
        total = root.findtext(".//totalCount")
        if total and page * 1000 >= int(total):
            break
        if len(items) < 1000:
            break
        page += 1
    return rows


def to_record(it, kind):
    apt = g(it, "aptNm", "아파트")
    umd = g(it, "umdNm", "법정동")
    if umd and DONG not in umd and umd not in DONG:
        return None
    tid = None
    for t in TARGETS:
        if any(norm(k) in norm(apt) for k in t["keys"]):
            tid = t["id"]; break
    if not tid:
        return None
    try:
        area = float(g(it, "excluUseAr", "전용면적") or 0)
    except ValueError:
        area = 0.0
    y = g(it, "dealYear", "년"); m = g(it, "dealMonth", "월"); d = g(it, "dealDay", "일")
    if not (y and m and d):
        return None
    rec = {
        "tid": tid, "ym": f"{int(y)}{int(m):02d}", "day": f"{int(d):02d}",
        "area": round(area, 2), "pyeong": round(area / EFF / 3.3058) if area else 0,
        "floor": (g(it, "floor", "층") or "").strip(),
    }
    if kind == "sale":
        rec["amount"] = int((g(it, "dealAmount", "거래금액") or "0").replace(",", "") or 0)
    else:
        rent = int((g(it, "monthlyRent", "월세금액", "월세") or "0").replace(",", "") or 0)
        if rent != 0:       # 전세만
            return None
        rec["amount"] = int((g(it, "deposit", "보증금액", "보증금") or "0").replace(",", "") or 0)
    return rec


def collect():
    months = prev_two_months()
    sales, jeonse = [], []
    for ymd in months:
        for it in fetch(TRADE_URL, ymd):
            r = to_record(it, "sale")
            if r: sales.append(r)
        for it in fetch(RENT_URL, ymd):
            r = to_record(it, "jeonse")
            if r: jeonse.append(r)
    return months, sales, jeonse


def demo(months):
    a, b = months
    S = lambda tid, ar, ym, dy, amt, fl: {"tid": tid, "ym": ym, "day": dy, "area": ar,
        "pyeong": round(ar / EFF / 3.3058), "floor": fl, "amount": amt}
    sales = [
        S("rmadp", 84.97, a, "12", 425000, "14"), S("rmadp", 114.96, b, "08", 538000, "9"),
        S("reelle", 84.91, b, "19", 408000, "15"),
        S("dongbu", 121.74, a, "22", 460000, "7"),
        S("ipark", 84.99, a, "16", 360000, "10"), S("ipark", 149.78, b, "27", 585000, "18"),
    ]
    jeonse = [
        S("rmadp", 84.97, a, "18", 205000, "11"),
        S("reelle", 59.93, b, "11", 150000, "5"),
        S("ipark", 84.99, a, "29", 160000, "9"),
    ]
    return sales, jeonse


def main():
    months = prev_two_months()
    is_demo = not KEY
    if is_demo:
        print("MOLIT_KEY 없음 → 샘플 데이터 생성")
        sales, jeonse = demo(months)
    else:
        months, sales, jeonse = collect()

    def pack(tid, arr):
        rows = [r for r in arr if r["tid"] == tid]
        rows.sort(key=lambda r: r["ym"] + r["day"], reverse=True)
        return [{k: v for k, v in r.items() if k != "tid"} for r in rows]

    targets = [{"id": t["id"], "name": t["name"], "built": t["built"],
                "sale": pack(t["id"], sales), "jeonse": pack(t["id"], jeonse)} for t in TARGETS]

    kst = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)
    data = {
        "generated": kst.strftime("%Y-%m-%d %H:%M KST"),
        "window": f"{months[0][:4]}.{months[0][4:]} ~ {months[1][:4]}.{months[1][4:]}",
        "efficiency": EFF,
        "demo": is_demo,
        "targets": targets,
    }
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"data.json 작성 완료 · 매매 {len(sales)}건 · 전세 {len(jeonse)}건 · {data['window']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("실패:", e, file=sys.stderr)
        sys.exit(1)
