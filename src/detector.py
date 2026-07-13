class MissingToothDetector:
    def __init__(self):
        """
        Dental_010: Missing & Supernumerary Teeth Detection Module
        008 모듈(치아 분할)에서 검출된 FDI 치식 번호 리스트를 입력받아
        정상 성인 치식(32개)과 대조하여 결손치 및 과잉치를 Rule-based로 식별합니다.
        """
        # 성인 영구치 기준 정상 치식 리스트 (11~18, 21~28, 31~38, 41~48)
        self.standard_adult_teeth = set(
            [10 + i for i in range(1, 9)] +
            [20 + i for i in range(1, 9)] +
            [30 + i for i in range(1, 9)] +
            [40 + i for i in range(1, 9)]
        )

    def detect(self, detected_fdi_list):
        """
        입력된 FDI 리스트를 기반으로 결손치와 과잉치를 분류합니다.
        
        Args:
            detected_fdi_list (list): 008 모듈에서 판독된 치아 번호들의 리스트
            
        Returns:
            dict: 결손치(missing) 및 과잉치/오류(supernumerary_or_error) 리스트
        """
        detected_set = set(detected_fdi_list)
        
        # 1. 결손치 (Missing Teeth) - 정상 치식에 있는데 검출되지 않은 치아
        missing_teeth = sorted(list(self.standard_adult_teeth - detected_set))
        
        # 2. 과잉치 또는 008 모듈 인식 오류 (Supernumerary or FP)
        # 정상 영구치 범위를 벗어난 번호 (예: 99번 등 오류 픽셀, 혹은 과잉치)
        supernumerary = sorted(list(detected_set - self.standard_adult_teeth))
        
        return {
            "missing_teeth": missing_teeth,
            "supernumerary_or_error": supernumerary
        }
