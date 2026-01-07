from typing import Tuple, Optional


def classify_make_model(frame, bbox: Tuple[int, int, int, int]) -> Tuple[Optional[str], float]:
    """
    Базовый классификатор марки/модели.
    В MVP возвращает "Unknown" с низкой уверенностью.
    Архитектурно подготовлено для улучшения модели.
    """
    # TODO: Интеграция с моделью классификации марок/моделей
    # Пока возвращаем Unknown
    return None, 0.0

