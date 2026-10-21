# Dental_010 (Missing & Supernumerary Teeth Detection)

![Status](https://img.shields.io/badge/Status-Rule--Based%20Heuristic-yellowgreen) ![Python](https://img.shields.io/badge/Python-3.12%2B-blue) ![Backend](https://img.shields.io/badge/Backend-Set%20Logic%20%2B%20Spatial%20Gap%20Heuristic-blue) ![License](https://img.shields.io/badge/License-MIT-green) ![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD%20Pipeline-passing-brightgreen?logo=github)

이 모듈은 `Dental_008` (Instance Segmentation & FDI Numbering) 모듈에서 산출된 치아 FDI 번호와 바운딩 박스 좌표를 바탕으로 결손치(Missing Teeth) 및 과잉치(Supernumerary Teeth)를 2단계 기하학적 규칙(Rule-based Heuristic)으로 판별하는 모듈입니다.

## 통합 아키텍처 및 알고리즘 (Unified Heuristic Architecture)

기존 `Dental_Panoramic_Reader/modules/dental_010_heuristic.py`에 분리되어 있던 실사용 공간 검증 로직을 본 저장소의 `src/detector.py`로 일원화하였습니다.

1. [1단계: 성인 32개 영구치 집합 차집합 (`MissingToothDetector.detect`)]:
   - 표준 영구치 집합(`11~18, 21~28, 31~38, 41~48`)과 검출된 FDI 집합의 차집합으로 1차 결손 후보(`candidate_missing`) 및 범위 외 번호(`supernumerary_or_error`)를 추출합니다.
2. [2단계: 최소 검출 치아 수 안전 가드 (`min_teeth_guard = 8`)]:
   - 영상 잘림(Truncation)이나 심한 아티팩트로 인해 검출된 치아 수가 `8개 미만`인 경우, 결손치 확정(`verified_missing`)을 유보하고 `UNVERIFIED_INSUFFICIENT_TEETH`로 격리합니다.
3. [3단계: 최후방 구치부 편측 인접치 부재 격리 (`POSTERIOR_DISTAL_TEETH`)]:
   - 제2·제3대구치(`#17, #18, #27, #28, #37, #38, #47, #48`)는 원심측(Distal) 인접 기준 치아가 없거나 미맹출·발치 빈도가 높으므로 무조건적인 결손 확진에서 제외하고 `uncertain_missing` (`UNCERTAIN_DISTAL_MISSING`)으로 분리합니다.
4. [4단계: 동적 정중선 추정 및 인접 치간 거리 비율 검증 (`verify_missing_teeth` / `evaluate_missing_teeth_from_boxes`)]:
   - 중절치(`#11, #21, #31, #41`) 바운딩 박스 중심으로부터 동적 정중선(`midline_x`)을 추정합니다.
   - 결손 후보 치아의 근심(Mesial) 및 원심(Distal) 인접치가 모두 존재할 때 중심간 거리 비율(`r_gap > 0.65` 또는 인접치 폭 대비 `gap_ratio >= 1.55`)을 충족하는 경우에만 `verified_missing`으로 확정하고, 교정 발치 후 치아 이동으로 공간이 닫힌 경우에는 `UNCERTAIN_DRIFT_OR_IMPACTION`으로 분류합니다.

## 벤치마크 및 검증 결과 (Benchmark & Validation)

- [통합 벤치마크 (`260903_2205_Dental_Modules_Comprehensive_Benchmark_Report.md` & `10_cases_quantitative_benchmark.json`)]:
  - 32개 영구치 차집합 연산 정합성: `100%`
  - 최후방 구치(`#18, #28, #38, #48` 등) 미맹출 오판 방어 격리율: `100%`
  - 복합 파노라마(`panoramic-x-ray-thegem-blog-default.jpg`) 과잉치(`#19, #29`) 골드 어노테이션 대조 결과: `#29` 후보 검출(`candidate_iou = 0.16 < 0.25`) 및 `#19` 미검출로, 과잉치 직접 시각 탐지는 선행 세그멘테이션(`Dental_008`)의 클래스 정의에 종속됨을 확인하고 한계점으로 명시함.
- [단위 테스트 (`tests/test_detector.py`)]:
  - 32개 영구치 차집합 하위 호환성, `< 8` 최소 치아 수 안전 가드, 최후방 구치 격리, 인접 갭 비율(`gap_ratio >= 1.55`) 확정 및 교정 공간 폐쇄(`gap_ratio < 1.55`) 유보 시나리오를 검증합니다.

## 한계점 (Limitations)
1. [선행 분할 모듈(`Dental_008`) 의존성]: 본 모듈은 `Dental_008`이 출력한 FDI 번호와 바운딩 박스를 입력으로 사용하므로, 선행 모듈에서 FDI 치식 밀림(Shift)이 발생하면 결손 위치 추정에 영향을 받습니다.
2. [교정 발치 공간 폐쇄]: 소구치 발치 교정 등으로 치간 공隙이 완전히 닫힌 경우, 기하학적 갭 비율이 임계값 미만으로 측정되어 `uncertain_missing`으로 분류됩니다.

## 설치 및 실행 방법
```bash
pip install -r requirements.txt
pytest tests/test_detector.py -v
```

## 가중치 파일 안내
본 모듈은 가중치 모델이 불필요한 룰베이스/기하학 휴리스틱 모듈이므로, 별도의 딥러닝 가중치 파일이 요구되지 않습니다.

## 연구용 실행 주의사항
- 기본 실행 주소: 127.0.0.1 (로컬 전용)
- 외부 공개/상용 배포 금지
- API 키·토큰은 환경변수로만 관리
- 오픈 데이터셋 외 민감 의료데이터 사용 금지
- 외부 접근이 필요하면 ALLOW_EXTERNAL_ACCESS=true 로만 명시적 허용
