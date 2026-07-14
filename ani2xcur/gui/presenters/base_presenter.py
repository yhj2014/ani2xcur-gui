"""基础 Presenter"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class BasePresenter:
    """Presenter 基类"""

    def __init__(self):
        self._view: Any = None

    def attach_view(self, view: Any):
        self._view = view
        logger.debug("视图已绑定: %s", type(view).__name__)

    def detach_view(self):
        self._view = None

    @property
    def view(self) -> Any:
        return self._view
