"""主窗口 Presenter"""

import logging

from ani2xcur.gui.presenters.base_presenter import BasePresenter
from ani2xcur.gui.presenters.convert_presenter import ConvertPresenter
from ani2xcur.gui.presenters.manage_presenter import ManagePresenter

logger = logging.getLogger(__name__)


class MainPresenter(BasePresenter):
    """主窗口 Presenter"""

    def __init__(self):
        super().__init__()
        self.convert_presenter = ConvertPresenter()
        self.manage_presenter = ManagePresenter()

    def attach_view(self, view):
        super().attach_view(view)
        logger.debug("MainPresenter 已绑定视图")
