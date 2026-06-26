#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
국토부 아파트 실거래(매매/전세) 자동 수집 → data.json
매월 12일: 직전2개월 전체 + 당월 1~12일 신고분
매월 28일: 직전2개월 전체 + 당월 1~28일 신고분 → archive/YYYY-MM.json 에 전월 완성본 저장
환경변수 MOLIT_KEY 에 공공데이터포털 '일반 인증키(Decoding)' 값을 넣어 실행.
"""
import os, json, datetime, sys
import xml.etree.ElementTree as ET
import urllib.request, urllib.parse

KEY = os.environ.get("MOLIT_KEY", "").strip()
EFF = 0.74  # 전용률 가정(평형 추정)

# (id, name, keys[], lawd_cd, dong(str|list), built, units, loc)
TARGETS = [
    # ───────── 강남구 대치동 (11680) ─────────
    {"id":"daechi-palace","name":"래미안대치팰리스","keys":["래미안대치팰리스"],"lawd":"11680","dong":"대치동","built":"2015","units":None,"loc":"강남구 대치동"},
    {"id":"daechi-reelle","name":"대치르엘","keys":["대치르엘"],"lawd":"11680","dong":"대치동","built":"2023","units":None,"loc":"강남구 대치동"},
    {"id":"daechi-dongbu","name":"동부센트레빌","keys":["동부센트레빌"],"lawd":"11680","dong":"대치동","built":"2005","units":None,"loc":"강남구 대치동"},
    {"id":"daechi-ipark","name":"대치아이파크","keys":["대치아이파크"],"lawd":"11680","dong":"대치동","built":"2008","units":None,"loc":"강남구 대치동"},
    {"id":"daechi-skview","name":"대치SK뷰","keys":["대치SK뷰","대치에스케이뷰"],"lawd":"11680","dong":"대치동","built":"2017","units":239,"loc":"강남구 대치동"},
    {"id":"daechi-samsung1","name":"대치삼성1차","keys":["대치삼성1"],"lawd":"11680","dong":"대치동","built":"2000","units":960,"loc":"강남구 대치동"},
    {"id":"daechi-hyundai","name":"대치현대","keys":["대치현대"],"lawd":"11680","dong":"대치동","built":"1999","units":630,"loc":"강남구 대치동"},
    {"id":"daechi-pugio-summit","name":"대치푸르지오써밋","keys":["대치푸르지오써밋"],"lawd":"11680","dong":"대치동","built":"2023","units":489,"loc":"강남구 대치동"},
    {"id":"daechi-hi-stern","name":"래미안대치하이스턴","keys":["래미안대치하이스턴","대치하이스턴"],"lawd":"11680","dong":"대치동","built":"2014","units":354,"loc":"강남구 대치동"},
    {"id":"daechi-eunma","name":"은마","keys":["은마"],"lawd":"11680","dong":"대치동","built":"1979","units":4424,"loc":"강남구 대치동"},
    {"id":"gaepo-wooseong","name":"개포우성1·2차","keys":["개포우성1","개포우성2"],"lawd":"11680","dong":["대치동","개포동"],"built":"1983","units":1140,"loc":"강남구 대치/개포동"},
    {"id":"seonkyung","name":"선경1·2차","keys":["선경1","선경2"],"lawd":"11680","dong":"대치동","built":"1983","units":1034,"loc":"강남구 대치동"},
    {"id":"mido","name":"한보미도맨션1·2차","keys":["한보미도맨션","미도맨션"],"lawd":"11680","dong":"대치동","built":"1983","units":2436,"loc":"강남구 대치동"},

    # ───────── 강남구 도곡동 ─────────
    {"id":"dogok-rexle","name":"도곡렉슬","keys":["도곡렉슬"],"lawd":"11680","dong":"도곡동","built":"2006","units":3002,"loc":"강남구 도곡동"},
    {"id":"tower-palace2","name":"타워팰리스2차","keys":["타워팰리스2"],"lawd":"11680","dong":"도곡동","built":"2003","units":813,"loc":"강남구 도곡동"},

    # ───────── 강남구 역삼동 ─────────
    {"id":"gn-central-ipark","name":"강남센트럴아이파크","keys":["강남센트럴아이파크"],"lawd":"11680","dong":"역삼동","built":"2022","units":499,"loc":"강남구 역삼동"},
    {"id":"yeoksam-rmian","name":"역삼래미안","keys":["역삼래미안"],"lawd":"11680","dong":"역삼동","built":"2005","units":1050,"loc":"강남구 역삼동"},
    {"id":"rmian-graytun3","name":"래미안그레이튼3차","keys":["래미안그레이튼3","그레이튼3"],"lawd":"11680","dong":"역삼동","built":"2009","units":476,"loc":"강남구 역삼동"},
    {"id":"yeoksam-zai","name":"역삼자이","keys":["역삼자이"],"lawd":"11680","dong":"역삼동","built":"2016","units":408,"loc":"강남구 역삼동"},
    {"id":"gaenari-skview","name":"개나리SK뷰","keys":["개나리SK뷰","개나리에스케이뷰"],"lawd":"11680","dong":"역삼동","built":"2012","units":240,"loc":"강남구 역삼동"},

    # ───────── 강남구 개포동 ─────────
    {"id":"dh-firstier","name":"디에이치퍼스티어아이파크","keys":["디에이치퍼스티어아이파크","퍼스티어아이파크"],"lawd":"11680","dong":"개포동","built":"2023","units":6702,"loc":"강남구 개포동"},
    {"id":"rmian-blestige","name":"래미안블레스티지","keys":["래미안블레스티지","블레스티지"],"lawd":"11680","dong":"개포동","built":"2019","units":1957,"loc":"강남구 개포동"},
    {"id":"gaepo-rmian-forest","name":"개포래미안포레스트","keys":["개포래미안포레스트"],"lawd":"11680","dong":"개포동","built":"2020","units":2296,"loc":"강남구 개포동"},
    {"id":"dh-honor-hills","name":"디에이치아너힐스","keys":["디에이치아너힐스","아너힐스"],"lawd":"11680","dong":"개포동","built":"2019","units":1320,"loc":"강남구 개포동"},
    {"id":"gaepo-zai-pres","name":"개포자이프레지던스","keys":["개포자이프레지던스","자이프레지던스"],"lawd":"11680","dong":"개포동","built":"2023","units":3375,"loc":"강남구 개포동"},

    # ───────── 강남구 일원동 ─────────
    {"id":"dh-zai-gaepo","name":"디에이치자이개포","keys":["디에이치자이개포"],"lawd":"11680","dong":"일원동","built":"2021","units":1996,"loc":"강남구 일원동"},
    {"id":"rmian-lucheheim","name":"래미안개포루체하임","keys":["래미안개포루체하임","루체하임"],"lawd":"11680","dong":"일원동","built":"2018","units":850,"loc":"강남구 일원동"},
    {"id":"mokryun-town","name":"목련타운","keys":["목련타운"],"lawd":"11680","dong":"일원동","built":"1993","units":650,"loc":"강남구 일원동"},
    {"id":"pureun-village","name":"푸른마을","keys":["푸른마을"],"lawd":"11680","dong":"일원동","built":"1994","units":930,"loc":"강남구 일원동"},
    {"id":"saemter-village","name":"샘터마을","keys":["샘터마을"],"lawd":"11680","dong":"일원동","built":"1993","units":628,"loc":"강남구 일원동"},

    # ───────── 강남구 수서동 ─────────
    {"id":"kkachi-village","name":"까치마을","keys":["까치마을"],"lawd":"11680","dong":"수서동","built":"1993","units":1404,"loc":"강남구 수서동"},
    {"id":"suseo-samik","name":"삼익","keys":["삼익"],"lawd":"11680","dong":"수서동","built":"1992","units":645,"loc":"강남구 수서동"},
    {"id":"suseo-shindonga","name":"신동아","keys":["신동아"],"lawd":"11680","dong":"수서동","built":"1992","units":1162,"loc":"강남구 수서동"},
    {"id":"suseo-haarum","name":"수서한아름","keys":["수서한아름","한아름"],"lawd":"11680","dong":"수서동","built":"1993","units":498,"loc":"강남구 수서동"},

    # ───────── 강남구 삼성동 ─────────
    {"id":"ss-central-ipark","name":"삼성동센트럴아이파크","keys":["삼성동센트럴아이파크"],"lawd":"11680","dong":"삼성동","built":"2018","units":416,"loc":"강남구 삼성동"},
    {"id":"rmian-la-classy","name":"래미안라클래시","keys":["래미안라클래시","라클래시"],"lawd":"11680","dong":"삼성동","built":"2021","units":679,"loc":"강남구 삼성동"},
    {"id":"acro-samsung","name":"아크로삼성","keys":["아크로삼성"],"lawd":"11680","dong":"삼성동","built":"2025","units":419,"loc":"강남구 삼성동"},
    {"id":"ss-hillstate1","name":"삼성동힐스테이트1단지","keys":["삼성동힐스테이트1","힐스테이트1단지"],"lawd":"11680","dong":"삼성동","built":"2008","units":1144,"loc":"강남구 삼성동"},

    # ───────── 강남구 청담동 ─────────
    {"id":"chungdam-zai","name":"청담자이","keys":["청담자이"],"lawd":"11680","dong":"청담동","built":"2011","units":708,"loc":"강남구 청담동"},
    {"id":"chungdam-reelle","name":"청담르엘","keys":["청담르엘"],"lawd":"11680","dong":"청담동","built":"2025","units":1261,"loc":"강남구 청담동"},

    # ───────── 강남구 압구정동 ─────────
    {"id":"ap-misung1","name":"미성1차","keys":["미성1"],"lawd":"11680","dong":"압구정동","built":"1982","units":322,"loc":"강남구 압구정동"},
    {"id":"ap-misung2","name":"미성2차","keys":["미성2"],"lawd":"11680","dong":"압구정동","built":"1987","units":911,"loc":"강남구 압구정동"},
    {"id":"ap-shinhyundae","name":"신현대 9·11·12차","keys":["신현대"],"lawd":"11680","dong":"압구정동","built":"1982","units":1924,"loc":"강남구 압구정동"},
    {"id":"ap-hyundae67","name":"현대 6·7차","keys":["현대6","현대7"],"lawd":"11680","dong":"압구정동","built":"1978","units":1288,"loc":"강남구 압구정동"},
    {"id":"ap-yd-hanyang1","name":"영동한양1차","keys":["영동한양1"],"lawd":"11680","dong":"압구정동","built":"1977","units":936,"loc":"강남구 압구정동"},
    {"id":"ap-hanyang5","name":"한양5차","keys":["한양5"],"lawd":"11680","dong":"압구정동","built":"1979","units":343,"loc":"강남구 압구정동"},

    # ───────── 송파구 (11710) ─────────
    {"id":"helio-city","name":"헬리오시티","keys":["헬리오시티"],"lawd":"11710","dong":"가락동","built":"2018","units":9510,"loc":"송파구 가락동"},
    {"id":"park-rio","name":"파크리오","keys":["파크리오"],"lawd":"11710","dong":"신천동","built":"2008","units":6864,"loc":"송파구 신천동"},
    {"id":"jamsil-reelle","name":"잠실르엘","keys":["잠실르엘"],"lawd":"11710","dong":"신천동","built":"2026","units":1865,"loc":"송파구 신천동"},
    {"id":"jamsil-rmian-ipark","name":"잠실래미안아이파크","keys":["잠실래미안아이파크"],"lawd":"11710","dong":"신천동","built":"2026","units":2678,"loc":"송파구 신천동"},
    {"id":"jamsil-els","name":"잠실엘스","keys":["잠실엘스","엘스"],"lawd":"11710","dong":"잠실동","built":"2008","units":5678,"loc":"송파구 잠실동"},
    {"id":"trizium","name":"트리지움","keys":["트리지움"],"lawd":"11710","dong":"잠실동","built":"2008","units":3696,"loc":"송파구 잠실동"},
    {"id":"rissents","name":"리센츠","keys":["리센츠"],"lawd":"11710","dong":"잠실동","built":"2008","units":5563,"loc":"송파구 잠실동"},

    # ───────── 강동구 (11740) ─────────
    {"id":"olympic-foreon","name":"올림픽파크포레온","keys":["올림픽파크포레온","파크포레온"],"lawd":"11740","dong":"둔촌동","built":"2024","units":12032,"loc":"강동구 둔촌동"},
    {"id":"theshop-doonchon","name":"더샵둔촌포레","keys":["더샵둔촌포레","둔촌포레"],"lawd":"11740","dong":"둔촌동","built":"2024","units":572,"loc":"강동구 둔촌동"},
    {"id":"doonchon-pugio","name":"둔촌푸르지오","keys":["둔촌푸르지오"],"lawd":"11740","dong":"둔촌동","built":"2010","units":800,"loc":"강동구 둔촌동"},
    {"id":"godeok-grasium","name":"고덕그라시움","keys":["고덕그라시움","그라시움"],"lawd":"11740","dong":"고덕동","built":"2019","units":4932,"loc":"강동구 고덕동"},
    {"id":"godeok-central-pugio","name":"고덕센트럴푸르지오","keys":["고덕센트럴푸르지오"],"lawd":"11740","dong":"고덕동","built":"2020","units":656,"loc":"강동구 고덕동"},

    # ───────── 서초구 (11650) ─────────
    {"id":"rmian-onebailey","name":"래미안원베일리","keys":["래미안원베일리","원베일리"],"lawd":"11650","dong":"반포동","built":"2023","units":2990,"loc":"서초구 반포동"},
    {"id":"acro-riverpark","name":"아크로리버파크","keys":["아크로리버파크"],"lawd":"11650","dong":"반포동","built":"2016","units":1612,"loc":"서초구 반포동"},
    {"id":"rmian-furstige","name":"래미안퍼스티지","keys":["래미안퍼스티지","퍼스티지"],"lawd":"11650","dong":"반포동","built":"2009","units":2444,"loc":"서초구 반포동"},
    {"id":"banpo-zai","name":"반포자이","keys":["반포자이"],"lawd":"11650","dong":"반포동","built":"2009","units":3410,"loc":"서초구 반포동"},
    {"id":"shinbanpo4","name":"신반포4차","keys":["신반포4"],"lawd":"11650","dong":"잠원동","built":"1979","units":1212,"loc":"서초구 잠원동"},
    {"id":"shinbanpo-zai","name":"신반포자이","keys":["신반포자이"],"lawd":"11650","dong":"잠원동","built":"2018","units":607,"loc":"서초구 잠원동"},
    {"id":"maple-zai","name":"메이플자이","keys":["메이플자이"],"lawd":"11650","dong":"잠원동","built":"2025","units":3307,"loc":"서초구 잠원동"},
    {"id":"banpo-reelle","name":"반포르엘","keys":["반포르엘"],"lawd":"11650","dong":"잠원동","built":"2022","units":None,"loc":"서초구 잠원동"},
]

TRADE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
RENT_URL  = "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"


def norm(s): return (s or "").replace(" ", "").lower()


def calc_months(ref=None):
    """
    실행일 기준 수집 대상 월 목록 반환.
    - 항상 직전 2개월(full) + 당월(partial, 당일까지 신고분)을 수집
    - 반환: (months_list, run_day)
      months_list = ["YYYYMM", "YYYYMM", "YYYYMM"]  # 직전2 + 당월
    """
    ref = ref or datetime.date.today()
    months = []
    for k in (2, 1):
        mm, yy = ref.month - k, ref.year
        while mm <= 0:
            mm += 12; yy -= 1
        months.append(f"{yy}{mm:02d}")
    # 당월 추가
    months.append(f"{ref.year}{ref.month:02d}")
    return months, ref.day


def g(item, *tags):
    for t in tags:
        e = item.find(t)
        if e is not None and e.text:
            return e.text.strip()
    return ""


def fetch(url, ymd, lawd):
    rows, page = [], 1
    while True:
        qs = urllib.parse.urlencode({
            "serviceKey": KEY, "LAWD_CD": lawd, "DEAL_YMD": ymd,
            "pageNo": page, "numOfRows": 1000,
        })
        req = urllib.request.Request(f"{url}?{qs}", headers={"User-Agent": "molit-auto/1.0"})
        with urllib.request.urlopen(req, timeout=40) as r:
            raw = r.read().decode("utf-8", "replace")
        root = ET.fromstring(raw)
        code = root.findtext(".//resultCode") or root.findtext(".//returnReasonCode")
        if code and code not in ("00", "000"):
            msg = root.findtext(".//resultMsg") or root.findtext(".//returnAuthMsg") or raw[:200]
            raise RuntimeError(f"API 오류({code}) lawd={lawd} ymd={ymd}: {msg}")
        items = root.findall(".//item")
        if not items:
            break
        rows.extend(items)
        total = int(root.findtext(".//totalCount") or 0)
        if page * 1000 >= total:
            break
        page += 1
    return rows


def match_target(apt, umd):
    apt_n = norm(apt)
    for t in TARGETS:
        dongs = t["dong"] if isinstance(t["dong"], list) else [t["dong"]]
        if not any(d in (umd or "") for d in dongs):
            continue
        if any(norm(k) in apt_n for k in t["keys"]):
            return t["id"]
    return None


def to_record(it, kind):
    apt = g(it, "aptNm", "아파트")
    umd = g(it, "umdNm", "법정동")
    if not apt:
        return None
    tid = match_target(apt, umd)
    if not tid:
        return None
    try:
        area = float(g(it, "excluUseAr", "전용면적") or 0)
    except ValueError:
        area = 0.0
    y = g(it, "dealYear", "년"); m = g(it, "dealMonth", "월"); d = g(it, "dealDay", "일")
    if not (y and m and d):
        return None
    apt_dong = (g(it, "aptDong") or "").strip()
    rec = {
        "tid": tid, "ym": f"{int(y)}{int(m):02d}", "day": f"{int(d):02d}",
        "area": round(area, 2), "pyeong": round(area / EFF / 3.3058) if area else 0,
        "floor": (g(it, "floor", "층") or "").strip(),
        "apt_dong": apt_dong,
    }
    if kind == "sale":
        rec["amount"] = int((g(it, "dealAmount", "거래금액") or "0").replace(",", "") or 0)
    else:
        rent = int((g(it, "monthlyRent", "월세금액", "월세") or "0").replace(",", "") or 0)
        if rent != 0:
            return None
        rec["amount"] = int((g(it, "deposit", "보증금액", "보증금") or "0").replace(",", "") or 0)
        ct = g(it, "contractType", "계약구분") or ""
        rec["renew"] = "갱신" if "갱신" in ct else "신규"
    return rec


def collect(months):
    sales, jeonse = [], []
    lawds = sorted({t["lawd"] for t in TARGETS})
    for ymd in months:
        for lawd in lawds:
            for it in fetch(TRADE_URL, ymd, lawd):
                r = to_record(it, "sale")
                if r: sales.append(r)
            for it in fetch(RENT_URL, ymd, lawd):
                r = to_record(it, "jeonse")
                if r: jeonse.append(r)
    return sales, jeonse


def demo_rows(months):
    """API 키 없이 동작 확인용"""
    a, b, c = months[0], months[1], months[2]
    S = lambda tid, ar, ym, dy, amt, fl, ad="": {
        "tid": tid, "ym": ym, "day": dy, "area": ar,
        "pyeong": round(ar / EFF / 3.3058), "floor": fl, "amount": amt, "apt_dong": ad}
    sales = [
        S("daechi-palace", 84.97, a, "12", 425000, "14", "101"),
        S("daechi-palace", 114.96, b, "08", 538000, "9"),
        S("daechi-palace", 84.97, c, "05", 430000, "7", "203"),
        S("daechi-reelle", 84.91, b, "19", 408000, "15", "203"),
        S("daechi-dongbu", 121.74, a, "22", 460000, "7"),
        S("daechi-ipark", 84.99, a, "16", 360000, "10", "305"),
    ]
    J = lambda tid, ar, ym, dy, amt, fl, ad="", rv="신규": {
        "tid": tid, "ym": ym, "day": dy, "area": ar,
        "pyeong": round(ar / EFF / 3.3058), "floor": fl, "amount": amt, "apt_dong": ad, "renew": rv}
    jeonse = [
        J("daechi-palace", 84.97, a, "18", 205000, "11", "101", "신규"),
        J("daechi-ipark", 84.99, b, "29", 160000, "9", "", "갱신"),
        J("daechi-reelle", 84.91, c, "03", 200000, "12", "", "신규"),
    ]
    return sales, jeonse


def build_targets(sales, jeonse):
    """sales/jeonse 원시 레코드 → targets 리스트"""
    def pack(tid, arr):
        rows = [r for r in arr if r["tid"] == tid]
        rows.sort(key=lambda r: r["ym"] + r["day"], reverse=True)
        return [{k: v for k, v in r.items() if k != "tid"} for r in rows]

    targets = []
    for t in TARGETS:
        targets.append({
            "id": t["id"], "name": t["name"], "loc": t["loc"],
            "built": t["built"], "units": t["units"],
            "sale": pack(t["id"], sales),
            "jeonse": pack(t["id"], jeonse),
        })
    return targets


def main():
    ref = datetime.date.today()
    months, run_day = calc_months(ref)
    is_28 = (run_day == 28)   # 28일 실행 여부
    is_demo = not KEY

    if is_demo:
        print("MOLIT_KEY 없음 → 샘플 데이터 생성")
        sales, jeonse = demo_rows(months)
    else:
        sales, jeonse = collect(months)

    kst = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)

    # ── 직전 2개월 표시 (당월은 "~MM/DD" 로 표기)
    m_labels = [f"{m[:4]}.{m[4:]}" for m in months[:2]]
    cur_label = f"{months[2][:4]}.{months[2][4:]} (~{ref.month}/{ref.day})"
    window_str = f"{m_labels[0]} ~ {m_labels[1]} + {cur_label}"

    # ── data.json (항상 갱신: 직전2개월 전체 + 당월 당일까지)
    data = {
        "generated": kst.strftime("%Y-%m-%d %H:%M KST"),
        "window": window_str,
        "run_day": run_day,
        "efficiency": EFF,
        "demo": is_demo,
        "targets": build_targets(sales, jeonse),
    }
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"data.json 갱신 완료 · {window_str}")

    # ── 28일 실행: 전월 완성본을 archive/YYYY-MM.json 으로 저장
    if is_28:
        # 전월 = months[1] (직전 1개월 = 오늘 기준 바로 직전달)
        prev_ym = months[1]   # e.g. "202605"
        prev_label = f"{prev_ym[:4]}-{prev_ym[4:]}"   # "2026-05"

        # 전월 데이터만 필터
        prev_sales  = [r for r in sales  if r["ym"] == prev_ym]
        prev_jeonse = [r for r in jeonse if r["ym"] == prev_ym]

        archive_data = {
            "generated": kst.strftime("%Y-%m-%d %H:%M KST"),
            "month": prev_label,
            "efficiency": EFF,
            "targets": build_targets(prev_sales, prev_jeonse),
        }
        os.makedirs("archive", exist_ok=True)
        arch_path = f"archive/{prev_label}.json"
        with open(arch_path, "w", encoding="utf-8") as f:
            json.dump(archive_data, f, ensure_ascii=False, indent=1)
        print(f"archive 저장 완료 · {arch_path} ({len(prev_sales)}건 매매, {len(prev_jeonse)}건 전세)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("실패:", e, file=sys.stderr)
        sys.exit(1)
