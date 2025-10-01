"""
추가 질병 필드 처리를 위한 유틸리티 함수들
"""


def get_additional_disease_context(record):
    """
    추가 질병 필드를 original_data에 추가하는 함수

    Args:
        record: DiseaseRecord 인스턴스

    Returns:
        dict: additional_disease 관련 original_data
    """
    return {
        'additional_disease_name': record.original_additional_disease_name or '',
        'additional_disease_code': record.original_additional_disease_code or '',
    }


def save_additional_disease_fields(record, form_data):
    """
    추가 질병 필드를 저장하는 함수

    Args:
        record: DiseaseRecord 인스턴스
        form_data: POST 데이터

    Returns:
        tuple: (additional_disease_name, additional_disease_code, has_changes)
    """
    additional_disease_name = form_data.get('additional_disease', '').strip()
    additional_disease_code = form_data.get('additional_disease_code', '').strip()

    has_changes = False

    # 추가 질병명 변경 확인
    if additional_disease_name != (record.additional_disease_name or ''):
        record.additional_disease_name = additional_disease_name
        has_changes = True

    # 추가 질병 코드 변경 확인
    if additional_disease_code != (record.additional_disease_code or ''):
        record.additional_disease_code = additional_disease_code
        has_changes = True

    return additional_disease_name, additional_disease_code, has_changes
