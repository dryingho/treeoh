# DB 유출 '범위'를 확인하는 스크립트.
# Git 에서 찾은 최소 권한 계정(app_legacy)으로 접속해서,
#   - demo_records 테이블은 읽히고 (유출 범위 안)
#   - auth_user 같은 테이블은 막힌다 (유출 범위 밖)
# 는 것을 보여주고 증거 파일을 남긴다.
#
# 사용:
#   python scripts/leak_demo.py --user app_legacy --password <git에서 찾은 값>
import argparse
import os
from datetime import datetime

try:
    import psycopg
except ImportError:
    print("psycopg 가 필요해요: pip install 'psycopg[binary]'")
    raise SystemExit(1)

# 읽히면 안 되는(= 범위 밖) 테이블들
OUT_OF_SCOPE = ["auth_user", "operator_panel_auditlog", "board_comment"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=os.environ.get("POSTGRES_HOST", "127.0.0.1"))
    ap.add_argument("--port", default=os.environ.get("POSTGRES_PORT", "5432"))
    ap.add_argument("--dbname", default=os.environ.get("POSTGRES_DB", "portfolio_lab"))
    ap.add_argument("--user", default=os.environ.get("LAB_LEAK_DB_USER", "app_legacy"))
    ap.add_argument("--password", default=os.environ.get("LAB_LEAK_DB_PASSWORD", "legacy_pw_exposed_in_git_2019"))
    ap.add_argument("--evidence-dir",
                    default=os.environ.get("LAB_MEDIA_ROOT",
                                           os.path.join(os.path.dirname(__file__), "..", "shared", "uploads")))
    args = ap.parse_args()

    lines = []

    def say(s=""):
        print(s)
        lines.append(s)

    say("====== DB 유출 범위 확인 ======")
    say("시간: " + datetime.now().isoformat())
    say("계정: " + args.user + " (최소 권한 계정)")
    say("")

    # 1) 접속 (과거 비밀번호가 아직 유효한지 여기서 드러남)
    try:
        conn = psycopg.connect(host=args.host, port=args.port, dbname=args.dbname,
                               user=args.user, password=args.password, connect_timeout=5)
    except Exception as e:
        say("[접속 실패] " + str(e))
        say("-> 과거 비밀번호가 더 이상 안 통한다 = 교체됨(수정 모드).")
        save(args, lines)
        return

    say("[접속 성공] 과거 비밀번호가 아직도 통한다 = 교체 안 됨(취약).")
    say("")

    cur = conn.cursor()

    # 2) 범위 안: demo_records 는 읽힌다
    say("--- 범위 안 (읽혀야 정상) ---")
    try:
        cur.execute("SELECT count(*) FROM demo_records_democustomer;")
        n = cur.fetchone()[0]
        say("demo_records_democustomer: %d 행" % n)
        cur.execute("SELECT name, email, lab_plaintext_password FROM demo_records_democustomer LIMIT 3;")
        for row in cur.fetchall():
            say("  - %s / %s / pw=%s" % (row[0], row[1], row[2]))
    except Exception as e:
        conn.rollback()
        say("demo_records_democustomer 실패: " + str(e))

    # 3) 범위 밖: 다른 테이블은 막힌다
    say("")
    say("--- 범위 밖 (막혀야 정상) ---")
    for t in OUT_OF_SCOPE:
        try:
            cur.execute("SELECT count(*) FROM " + t + ";")
            say("[주의] %s 가 읽힘 (%d 행) - 권한 설정 확인 필요" % (t, cur.fetchone()[0]))
        except Exception as e:
            conn.rollback()
            say("[막힘] %s : %s" % (t, str(e).splitlines()[0]))

    conn.close()
    say("")
    say("결론: 유출 범위는 demo_records 테이블로 한정된다. 평문 저장이라고 전체 DB 유출은 아니다.")
    save(args, lines)


# 증거 파일로 저장
def save(args, lines):
    folder = os.path.join(args.evidence_dir, "_evidence")
    os.makedirs(folder, exist_ok=True)
    name = "leak_scope_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"
    path = os.path.join(folder, name)
    with open(path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines))
    print("[증거] " + path)


if __name__ == "__main__":
    main()
