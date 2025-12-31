# Synology Workflow Scripts

## Copy for YouTube (Upload Workflow)

이 스크립트는 NAS에 저장된 대용량 영상 파일을 유튜브 업로드 전용 폴더로 자동 복사하고, 진행 상황을 DB로 관리하며 Discord로 리포트를 전송하는 자동화 워크플로우입니다.

### ⚙️ 설치 및 설정 (Installation & Configuration)

이 프로젝트를 다운로드한 후, 사용자 환경에 맞게 설정을 변경해야 합니다.

1. **설정 파일 준비**:
   - `config(base).json` 파일의 이름을 `config.json`으로 변경합니다.
   - `config.json` 파일을 열어 본인의 Synology 경로와 Webhook 주소 등을 입력합니다.
     ```json
     {
         "source_dir": "/YOUR_SOURCE_FOLDER",
         "upload_dir": "/YOUR_UPLOAD_FOLDER",
         "completed_dir": "/YOUR_COMPLETED_FOLDER",
         "db_path": "/YOUR_DB_PATH/photo_workflow.db",
         "min_size_mb": 100,
         "webhook_url": "https://discord.com/api/webhooks/YOUR_DISCORD_WEBHOOK_URL",
         "extensions": [".mp4", ".mov", ".MP4", ".MOV"]
     }
     ```
   - **주의**: `config.json` 파일은 개인 정보를 포함하므로 외부에 공유되지 않도록 주의하세요 (`.gitignore`에 포함되어 있습니다).

2. **실행 권한 부여**:
   - `.sh` 스크립트가 실행될 수 있도록 권한을 변경합니다.
   ```bash
   chmod 755 copy_for_youtube.sh
   # 또는
   chmod +x copy_for_youtube.sh
   ```

3. **파일 위치 확인**:
   - `copy_for_youtube.py`와 `copy_for_youtube.sh` 파일은 반드시 **동일한 폴더**에 위치해야 합니다. (쉘 스크립트가 파이썬 스크립트를 상대 경로로 찾습니다.)

### 1. 주요 기능
- **자동 스캔**: 소스 폴더(config.json의 `source_dir`)에서 100MB 이상의 `.mp4`, `.mov` 파일을 검색합니다.
- **자동 복사**: 검색된 파일 중 아직 처리되지 않은 파일(Status 0)을 업로드 폴더(config.json의 `upload_dir`)로 복사합니다.
- **상태 추적**: SQLite 데이터베이스를 통해 파일의 처리 상태를 관리합니다.
- **완료 처리**: 유튜브 업로드가 완료되어 파일이 `Complete` 폴더(config.json의 `completed_dir`)로 이동되면, DB 상태를 업데이트합니다.
- **알림 전송 (옵션)**: `webhook_url`이 설정된 경우, 일일 작업 처리 현황을 Discord로 전송합니다.

### 2. 실행 방법 (Task Scheduler)

#### 표준 실행 (Standard Run)
주기적으로 실행되어 신규 파일을 스캔하고 복사 작업을 수행합니다.
```bash
bash /PATH/TO/YOUR/SCRIPT/copy_for_youtube.sh
```

#### 리포트 실행 (Report Run)
하루에 한 번(주로 밤/새벽) 실행하여 당일 처리 현황을 Discord로 알림을 보냅니다. `notify` 인자를 전달합니다.
*`webhook_url`이 설정되어 있어야 작동합니다.*
```bash
bash /PATH/TO/YOUR/SCRIPT/copy_for_youtube.sh notify
```

### 3. 상세 로직 및 경로 정보

| 항목 | 경로 / 설명 |
| :--- | :--- |
| **스크립트 위치** | `config.json`이 위치한 폴더 (Git 프로젝트 폴더) |
| **소스 폴더** | `source_dir` (config.json 설정값) |
| **타겟 폴더** | `upload_dir` (config.json 설정값) |
| **완료 폴더** | `completed_dir` (config.json 설정값) |
| **데이터베이스** | `db_path` (config.json 설정값) |
| **로그 히스토리** | DB 내 `history` 컬럼에 상태 변경 이력 기록 |

#### 상태(Status) 라이프사이클
1. **Status 0 (New)**: 소스 폴더에서 100MB 이상 영상 파일 발견. DB 등록.
2. **Status 1 (Copied)**: 타겟 폴더로 복사 완료. (업로드 대기 중)
3. **Status 2 (Completed)**: 타겟 폴더에서 파일이 사라지고 `Complete` 폴더에서 발견됨. (업로드 완료)