![Status](https://img.shields.io/badge/Status-v1.0%20Release-brightgreen) ![Python](https://img.shields.io/badge/Python-3.12%2B-blue) ![Backend](https://img.shields.io/badge/Backend-YOLOv8-red) ![UI](https://img.shields.io/badge/UI-Streamlit-orange) ![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD%20Pipeline-passing-brightgreen?logo=github)

# Dental_010 (Missing & Supernumerary Teeth Detection)

이 모듈은 Dental_008 (Instance Segmentation) 모듈에서 산출된 치식(FDI) 번호를 바탕으로 결손치(Missing Teeth) 및 과잉치(Supernumerary Teeth)를 Rule-based로 추정하는 모듈입니다.

## 기능 (Features)
- 008 모듈에서 출력된 FDI 번호 리스트를 입력받습니다.
- 성인 정상 치식 32개(11~18, 21~28, 31~38, 41~48)와 비교하여 집합의 차집합 연산을 통해 누락된 치식을 결손치로 식별합니다.

> [!WARNING]
> ## Limitations (현재 버전의 한계점)
> 1. **008 모듈 성능에의 완전한 종속성**: 본 모듈은 단순한 룰 기반 필터이므로 008 모듈이 FDI 번호를 오분류하면 결손치/과잉치 판별도 그대로 틀리게 됩니다.
> 2. **치식 밀림 현상 미반영**: 교정 발치(예: 소구치 발치) 이력이 있는 환자의 경우, 008 모듈이 공간이 닫힌 치열을 순차적으로 잘못 매핑할 확률이 높습니다 (예: 4번이 없는데 5번을 4번으로 인식). 
> 3. **검증(Validation) 불가**: 위와 같은 이유로, 오픈 데이터셋 수준에서는 F1 Score 등 신뢰성 있는 벤치마크 검증이 당장 불가능합니다. 자체적인 정밀한 데이터셋 구축과 수동 채점이 필요하므로 현재는 뼈대 코드만 제공되며 릴리스 보류(Hold) 상태입니다.

## 학습 환경 (Training Environment)
> **[학습 환경 사양]** 실질적 모델 학습은 **RTX 5080 + 라이젠9-6 9900x** 환경에서 진행되었습니다.

## 개요
이 레포지토리는 치과 AI 모듈러 시스템의 일부입니다.

## 설치 및 실행 방법
```bash
pip install -r requirements.txt
```


## 가중치 파일 안내
본 모듈은 가중치 모델이 불필요한 룰베이스/인프라/기하학 모듈이므로, 별도의 딥러닝 가중치 파일이 요구되지 않습니다.
