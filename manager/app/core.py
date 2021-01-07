# -*- coding: iso-8859-1 -*-
import logging

# Logger
logging.basicConfig(filename='manager.log',
                    level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] %(module)s: %(message)s')

logger = logging.getLogger(__name__)
