# -*- coding: iso-8859-1 -*-

from manager.app import app
from manager.app.core import logger


def main():
    app.run(debug=True, host='0.0.0.0', port=8000, use_reloader=False)


if __name__ == "__main__":
    logger.info("SERVER STARTED")
    main()